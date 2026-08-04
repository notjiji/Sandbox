"""Demo data definitions — shared between seed script and documentation."""

DEMO_ORG_SLUG = "demo-corp"
DEMO_PASSWORD = "DemoPassword1!"

DEMO_USERS: list[dict[str, str]] = [
    {
        "email": "owner@demo.sandbox",
        "first_name": "Alex",
        "last_name": "Owner",
        "role": "owner",
    },
    {
        "email": "admin@demo.sandbox",
        "first_name": "Casey",
        "last_name": "Admin",
        "role": "admin",
    },
    {
        "email": "analyst@demo.sandbox",
        "first_name": "Sam",
        "last_name": "Analyst",
        "role": "security_analyst",
    },
    {
        "email": "manager@demo.sandbox",
        "first_name": "Morgan",
        "last_name": "Manager",
        "role": "manager",
    },
    {
        "email": "viewer@demo.sandbox",
        "first_name": "Riley",
        "last_name": "Viewer",
        "role": "viewer",
    },
]
