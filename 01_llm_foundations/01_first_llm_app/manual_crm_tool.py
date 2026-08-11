from crm_tools import create_crm_lead


result = create_crm_lead(
    name="John Smith",
    title="CEO",
    company="ABC Manufacturing",
    lead_score=85,
)

print("\nReturned object:")
print(result)