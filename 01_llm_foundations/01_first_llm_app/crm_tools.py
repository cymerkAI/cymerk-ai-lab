from pydantic import BaseModel, Field, ValidationError


class CRMLead(BaseModel):
    name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    lead_score: int = Field(ge=0, le=100)


def validate_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
):
    try:
        lead = CRMLead(
            name=name,
            title=title,
            company=company,
            lead_score=lead_score,
        )

        return True, lead

    except ValidationError as error:
        return False, str(error)


def create_crm_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
    require_approval=True,
):

    valid, result = validate_lead(
        name=name,
        title=title,
        company=company,
        lead_score=lead_score,
    )

    if not valid:

        print("\nCRM VALIDATION FAILED")
        print(result)

        return {
            "success": False,
            "status": "validation_failed",
            "error": result,
        }

    lead = result

    if require_approval:

        print("\n")
        print("=" * 50)
        print("CYMERK HUMAN APPROVAL REQUIRED")
        print("=" * 50)

        print(f"Name:       {lead.name}")
        print(f"Title:      {lead.title}")
        print(f"Company:    {lead.company}")
        print(f"Lead score: {lead.lead_score}")

        print("=" * 50)

        approval = input(
            "Approve creation of this CRM lead? (y/n): "
        )

        if approval.lower() != "y":

            print("\nCRM ACTION REJECTED")

            return {
                "success": False,
                "status": "rejected",
                "message": "Human approval was not granted.",
            }

    crm_record = {
        "name": lead.name,
        "title": lead.title,
        "company": lead.company,
        "lead_score": lead.lead_score,
        "status": "New",
    }

    print("\nCRM TOOL EXECUTED")
    print("-----------------")
    print(f"Created lead: {lead.name}")
    print(f"Company: {lead.company}")
    print(f"Lead score: {lead.lead_score}")
    print(f"Status: {crm_record['status']}")

    return {
        "success": True,
        "status": "created",
        "record": crm_record,
    }