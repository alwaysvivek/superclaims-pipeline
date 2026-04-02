from typing import List, Optional
from pydantic import BaseModel, Field

class PageClassification(BaseModel):
    """Schema for single page classification."""
    page: int = Field(..., description="The 0-based index of the page")
    classification: str = Field(..., description="Document type: claim_forms, identity_document, itemized_bill, discharge_summary, etc.")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    reasoning: str = Field(..., description="Short explanation for the classification")

class IdentityExtraction(BaseModel):
    """Schema for identity document extraction."""
    patient_name: Optional[str] = Field(None, description="Full name of the patient")
    date_of_birth: Optional[str] = Field(None, description="DOB in YYYY-MM-DD or DD/MM/YYYY")
    age: Optional[str] = Field(None, description="Age of the patient")
    gender: Optional[str] = Field(None, description="Male, Female, or Other")
    id_type: Optional[str] = Field(None, description="Type of ID document (Aadhaar, PAN, etc.)")
    id_number: Optional[str] = Field(None, description="ID number")
    policy_number: Optional[str] = Field(None, description="Insurance policy number")
    insurer_name: Optional[str] = Field(None, description="Name of the insurance company")
    member_id: Optional[str] = Field(None, description="Member/Employee ID if available")
    contact_number: Optional[str] = Field(None, description="Phone number if available")
    email: Optional[str] = Field(None, description="Email address if available")
    address: Optional[str] = Field(None, description="Full address if available")
    relation_to_primary: Optional[str] = Field(None, description="Relationship to primary holder")

class DischargeExtraction(BaseModel):
    """Schema for discharge summary extraction."""
    hospital_name: Optional[str] = Field(None, description="Name of the hospital")
    admission_date: Optional[str] = Field(None, description="Date of admission")
    discharge_date: Optional[str] = Field(None, description="Date of discharge")
    diagnosis: Optional[str] = Field(None, description="Primary medical diagnosis")
    treating_physician: Optional[str] = Field(None, description="Name of the main doctor")
    procedures_performed: Optional[List[str]] = Field(default_factory=list, description="List of medical procedures or surgeries")

class LineItem(BaseModel):
    """Schema for a single bill line item."""
    description: str = Field(..., description="Description of the service or item")
    quantity: float = Field(1.0, description="Quantity")
    unit_price: float = Field(..., description="Price per unit")
    total: float = Field(..., description="Total amount for this line (qty * unit_price)")

class BillingExtraction(BaseModel):
    """Schema for itemized bill extraction."""
    hospital_name: Optional[str] = Field(None, description="Name of the provider")
    bill_number: Optional[str] = Field(None, description="Bill or invoice reference number")
    bill_date: Optional[str] = Field(None, description="Date of the bill")
    currency: str = Field("INR", description="Currency (default: INR)")
    line_items: List[LineItem] = Field(default_factory=list, description="Detailed list of items")
    subtotal: Optional[float] = Field(None, description="Sum of line items before tax/discount")
    tax: Optional[float] = Field(0.0, description="Tax amount")
    discount: Optional[float] = Field(0.0, description="Discount amount")
    grand_total: Optional[float] = Field(None, description="Final amount payable")
