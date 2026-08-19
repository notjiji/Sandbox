from __future__ import annotations

import secrets
import socket
import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

import dns.resolver
import httpx
from sqlalchemy.orm import Session

from app.assets.enums import AssetType, AssetVerificationMethod, AssetVerificationStatus
from app.assets.metadata import metadata_to_dict
from app.assets.models import Asset
from app.assets.repositories.asset_repository import get_asset_by_id
from app.assets.schemas import AssetVerificationSummary
from app.assets.validators import require_active_project
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember

TXT_PREFIX = "_sandbox-verify"
WELL_KNOWN_PATH = "/.well-known/sandbox-verification.txt"


class AssetVerificationService:
    def _get_asset(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Asset:
        require_active_project(db, membership, project_id)
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not asset:
            raise NotFoundError("Asset")
        return asset

    def get_status(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetVerificationSummary:
        asset = self._get_asset(db, membership, project_id=project_id, asset_id=asset_id)
        dns_record_name, http_challenge_url = self._challenge_hints(asset)
        return AssetVerificationSummary(
            method=asset.verification_method,
            status=asset.verification_status or AssetVerificationStatus.UNVERIFIED.value,
            challenge_token=asset.verification_token,
            dns_record_name=dns_record_name,
            http_challenge_url=http_challenge_url,
            requested_at=asset.verification_requested_at,
            verified_at=asset.verification_verified_at,
            last_error=asset.verification_last_error,
        )

    def start_challenge(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        method: AssetVerificationMethod,
    ) -> AssetVerificationSummary:
        asset = self._get_asset(db, membership, project_id=project_id, asset_id=asset_id)
        token = secrets.token_urlsafe(24)
        asset.verification_method = method.value
        asset.verification_status = AssetVerificationStatus.PENDING.value
        asset.verification_token = token
        asset.verification_requested_at = datetime.now(UTC)
        asset.verification_verified_at = None
        asset.verification_last_error = None
        db.add(asset)
        db.commit()
        db.refresh(asset)
        dns_record_name, http_challenge_url = self._challenge_hints(asset)
        return AssetVerificationSummary(
            method=method,
            status=AssetVerificationStatus.PENDING,
            challenge_token=token,
            dns_record_name=dns_record_name,
            http_challenge_url=http_challenge_url,
            message="Challenge created. Publish token, then call verify.",
            requested_at=asset.verification_requested_at,
        )

    def verify(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetVerificationSummary:
        asset = self._get_asset(db, membership, project_id=project_id, asset_id=asset_id)
        method = asset.verification_method
        token = asset.verification_token
        if not method or not token:
            raise ValidationAppError("No verification challenge exists for this asset")

        passed, error = self._run_check(asset, AssetVerificationMethod(method), token)
        asset.verification_status = (
            AssetVerificationStatus.VERIFIED.value
            if passed
            else AssetVerificationStatus.FAILED.value
        )
        asset.verification_verified_at = datetime.now(UTC) if passed else None
        asset.verification_last_error = None if passed else error
        db.add(asset)
        db.commit()
        db.refresh(asset)

        dns_record_name, http_challenge_url = self._challenge_hints(asset)
        return AssetVerificationSummary(
            method=asset.verification_method,
            status=asset.verification_status,
            challenge_token=asset.verification_token,
            dns_record_name=dns_record_name,
            http_challenge_url=http_challenge_url,
            message="Verification succeeded" if passed else "Verification failed",
            requested_at=asset.verification_requested_at,
            verified_at=asset.verification_verified_at,
            last_error=asset.verification_last_error,
        )

    def _run_check(
        self, asset: Asset, method: AssetVerificationMethod, token: str
    ) -> tuple[bool, str | None]:
        if method == AssetVerificationMethod.DOMAIN:
            domain = self._resolve_domain_target(asset)
            return self._verify_domain(domain)
        if method == AssetVerificationMethod.DNS_TXT:
            domain = self._resolve_domain_target(asset)
            return self._verify_dns_txt(domain, token)
        if method == AssetVerificationMethod.HTTP:
            host = self._resolve_http_host(asset)
            return self._verify_http_token(host, token)
        if method == AssetVerificationMethod.IP_OWNERSHIP:
            ip = self._resolve_ip_target(asset)
            return self._verify_ip_ownership(ip, token)
        return False, "Unsupported verification method"

    def _challenge_hints(self, asset: Asset) -> tuple[str | None, str | None]:
        method = asset.verification_method
        if method in {AssetVerificationMethod.DOMAIN.value, AssetVerificationMethod.DNS_TXT.value}:
            domain = self._resolve_domain_target(asset, raise_on_missing=False)
            if domain:
                return f"{TXT_PREFIX}.{domain}", None
        if method == AssetVerificationMethod.HTTP.value:
            host = self._resolve_http_host(asset, raise_on_missing=False)
            if host:
                return None, f"https://{host}{WELL_KNOWN_PATH}"
        if method == AssetVerificationMethod.IP_OWNERSHIP.value:
            ip = self._resolve_ip_target(asset, raise_on_missing=False)
            if ip:
                return None, f"http://{ip}{WELL_KNOWN_PATH}"
        return None, None

    def _resolve_domain_target(self, asset: Asset, *, raise_on_missing: bool = True) -> str | None:
        metadata = metadata_to_dict(asset.metadata_entries)
        if asset.type == AssetType.DOMAIN:
            return metadata.get("domain")
        if asset.type == AssetType.EMAIL_DOMAIN:
            return metadata.get("email_domain")
        if asset.type in {AssetType.WEBSITE, AssetType.API_ENDPOINT}:
            raw = metadata.get("url") or metadata.get("endpoint") or asset.external_identifier
            if raw:
                parsed = urlparse(raw if "://" in raw else f"https://{raw}")
                return parsed.hostname
        if raise_on_missing:
            raise ValidationAppError("Asset type does not support domain-based verification")
        return None

    def _resolve_http_host(self, asset: Asset, *, raise_on_missing: bool = True) -> str | None:
        metadata = metadata_to_dict(asset.metadata_entries)
        if asset.type == AssetType.WEBSITE:
            parsed = urlparse(metadata.get("url", ""))
            if parsed.hostname:
                return parsed.hostname
        if asset.type == AssetType.API_ENDPOINT:
            parsed = urlparse(metadata.get("endpoint", ""))
            if parsed.hostname:
                return parsed.hostname
        domain = self._resolve_domain_target(asset, raise_on_missing=False)
        if domain:
            return domain
        if raise_on_missing:
            raise ValidationAppError("Asset type does not support HTTP verification")
        return None

    def _resolve_ip_target(self, asset: Asset, *, raise_on_missing: bool = True) -> str | None:
        metadata = metadata_to_dict(asset.metadata_entries)
        if asset.type == AssetType.PUBLIC_IP:
            value = metadata.get("address") or asset.external_identifier
            if value:
                return value
        if raise_on_missing:
            raise ValidationAppError("Asset type does not support IP ownership verification")
        return None

    def _verify_domain(self, domain: str | None) -> tuple[bool, str | None]:
        if not domain:
            return False, "No domain available for verification"
        try:
            dns.resolver.resolve(domain, "NS", lifetime=6.0)
            return True, None
        except Exception as exc:
            return False, f"Domain ownership check failed: {exc}"

    def _verify_dns_txt(self, domain: str | None, token: str) -> tuple[bool, str | None]:
        if not domain:
            return False, "No domain available for DNS TXT verification"
        record = f"{TXT_PREFIX}.{domain}"
        try:
            answers = dns.resolver.resolve(record, "TXT", lifetime=8.0)
        except Exception as exc:
            return False, f"TXT record not found at {record}: {exc}"
        for answer in answers:
            for txt_value in answer.strings:
                if token in txt_value.decode("utf-8"):
                    return True, None
        return False, f"TXT record at {record} does not contain the verification token"

    def _verify_http_token(self, host: str | None, token: str) -> tuple[bool, str | None]:
        if not host:
            return False, "No HTTP host available for verification"
        candidates = [
            f"https://{host}{WELL_KNOWN_PATH}",
            f"http://{host}{WELL_KNOWN_PATH}",
        ]
        timeout = httpx.Timeout(8.0, connect=5.0)
        errors: list[str] = []
        for url in candidates:
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    response = client.get(url)
                if response.status_code >= 400:
                    errors.append(f"{url} returned {response.status_code}")
                    continue
                if token in response.text:
                    return True, None
                errors.append(f"{url} did not contain token")
            except Exception as exc:
                errors.append(f"{url} failed: {exc}")
        return False, "; ".join(errors)

    def _verify_ip_ownership(self, ip: str | None, token: str) -> tuple[bool, str | None]:
        if not ip:
            return False, "No IP available for verification"
        ptr_ok = False
        ptr_error: str | None = None
        try:
            ptr_host, _, _ = socket.gethostbyaddr(ip)
            ptr_ok = bool(ptr_host)
        except Exception as exc:
            ptr_error = str(exc)

        http_ok, http_error = self._verify_http_token(ip, token)
        if ptr_ok and http_ok:
            return True, None

        parts = []
        if not ptr_ok:
            parts.append(f"reverse DNS failed ({ptr_error})")
        if not http_ok:
            parts.append(f"HTTP challenge failed ({http_error})")
        return False, " and ".join(parts)


asset_verification_service = AssetVerificationService()
