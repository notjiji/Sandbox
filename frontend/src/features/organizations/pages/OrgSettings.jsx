import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Save } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError, unwrapData } from "@/shared/api/client";
import { organizationsApi } from "../api";

export default function OrgSettings() {
  const [form, setForm] = useState({
    name: "",
    description: "",
    industry: "",
    website: "",
    country: "",
    timezone: "",
  });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const org = unwrapData(await organizationsApi.getCurrent());
        if (!active) return;
        setForm({
          name: org.name ?? "",
          description: org.description ?? "",
          industry: org.industry ?? "",
          website: org.website ?? "",
          country: org.country ?? "",
          timezone: org.timezone ?? "",
        });
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load organization.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setAlert("");
    setSuccess("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await organizationsApi.updateCurrent({
        name: form.name.trim(),
        description: form.description.trim() || null,
        industry: form.industry.trim() || null,
        website: form.website.trim() || null,
        country: form.country.trim() || null,
        timezone: form.timezone.trim() || null,
      });
      setSuccess("Organization updated successfully.");
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to update organization.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardShell title="Organization Settings" subtitle="Manage your company profile.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}

      {loading ? (
        <div className="glass-panel animate-pulse p-8">Loading...</div>
      ) : (
        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="glass-panel space-y-5 p-8"
        >
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label htmlFor="name" className="terminal-text mb-2 block">name</label>
              <input id="name" name="name" value={form.name} onChange={handleChange} className="input-field" />
              <FormError message={errors.name} />
            </div>
            <div>
              <label htmlFor="industry" className="terminal-text mb-2 block">industry</label>
              <input id="industry" name="industry" value={form.industry} onChange={handleChange} className="input-field" />
            </div>
          </div>

          <div>
            <label htmlFor="description" className="terminal-text mb-2 block">description</label>
            <textarea id="description" name="description" rows={4} value={form.description} onChange={handleChange} className="input-field" />
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label htmlFor="website" className="terminal-text mb-2 block">website</label>
              <input id="website" name="website" value={form.website} onChange={handleChange} className="input-field" />
            </div>
            <div>
              <label htmlFor="country" className="terminal-text mb-2 block">country</label>
              <input id="country" name="country" value={form.country} onChange={handleChange} className="input-field" maxLength={2} />
            </div>
          </div>

          <div>
            <label htmlFor="timezone" className="terminal-text mb-2 block">timezone</label>
            <input id="timezone" name="timezone" value={form.timezone} onChange={handleChange} className="input-field" placeholder="Europe/London" />
          </div>

          <button type="submit" disabled={saving} className="btn-primary inline-flex items-center gap-2">
            <Save size={18} />
            {saving ? "Saving..." : "Save changes"}
          </button>
        </motion.form>
      )}
    </DashboardShell>
  );
}
