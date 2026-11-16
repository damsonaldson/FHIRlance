"""Generated FHIR R4 resource models (all 146 base R4 resources)."""
from __future__ import annotations
from typing import Annotated, Any, Literal
from pydantic import Field, StrictBool, StrictStr, model_validator
from fhirlance import types as fhir_types
from fhirlance.base import (
    DomainResourceBase, FHIRBaseModel, FHIRCode, FHIRDate, FHIRDateTime, FHIRDecimal,
    FHIRId, FHIRInstant, FHIRInteger, FHIRPositiveInt, FHIRTime, FHIRUnsignedInt,
)

class DomainResourceR4(DomainResourceBase):
    meta: fhir_types.Meta | None = None
    text: fhir_types.Narrative | None = None
    contained: Annotated[list[dict[str, Any]], Field(min_length=1)] | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None

class AccountCoverage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    coverage: fhir_types.Reference
    priority: FHIRPositiveInt | None = None
class AccountGuarantor(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    party: fhir_types.Reference
    onHold: StrictBool | None = None
    period: fhir_types.Period | None = None
class Account(DomainResourceR4):
    resourceType: Literal['Account']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'inactive', 'on-hold', 'unknown']
    type: fhir_types.CodeableConcept | None = None
    name: StrictStr | None = None
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    servicePeriod: fhir_types.Period | None = None
    coverage: Annotated[list[AccountCoverage], Field(min_length=1)] | None = None
    owner: fhir_types.Reference | None = None
    description: StrictStr | None = None
    guarantor: Annotated[list[AccountGuarantor], Field(min_length=1)] | None = None
    partOf: fhir_types.Reference | None = None

class ActivityDefinitionParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['device', 'patient', 'practitioner', 'related-person']
    role: fhir_types.CodeableConcept | None = None
class ActivityDefinitionDynamicValue(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    path: StrictStr
    expression: fhir_types.Expression
class ActivityDefinition(DomainResourceR4):
    resourceType: Literal['ActivityDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    library: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    kind: Literal['Appointment', 'AppointmentResponse', 'CarePlan', 'Claim', 'CommunicationRequest', 'Contract', 'DeviceRequest', 'EnrollmentRequest', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'SupplyRequest', 'Task', 'VisionPrescription'] | None = None
    profile: StrictStr | None = None
    code: fhir_types.CodeableConcept | None = None
    intent: Literal['directive', 'filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order'] | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    doNotPerform: StrictBool | None = None
    timingTiming: fhir_types.Timing | None = None
    timingDateTime: FHIRDateTime | None = None
    timingAge: fhir_types.Age | None = None
    timingPeriod: fhir_types.Period | None = None
    timingRange: fhir_types.Range | None = None
    timingDuration: fhir_types.Duration | None = None
    location: fhir_types.Reference | None = None
    participant: Annotated[list[ActivityDefinitionParticipant], Field(min_length=1)] | None = None
    productReference: fhir_types.Reference | None = None
    productCodeableConcept: fhir_types.CodeableConcept | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    dosage: Annotated[list[fhir_types.Dosage], Field(min_length=1)] | None = None
    bodySite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specimenRequirement: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    observationRequirement: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    observationResultRequirement: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    transform: StrictStr | None = None
    dynamicValue: Annotated[list[ActivityDefinitionDynamicValue], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ActivityDefinition':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        _present = sum(1 for _f in ('timingTiming', 'timingDateTime', 'timingAge', 'timingPeriod', 'timingRange', 'timingDuration',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        _present = sum(1 for _f in ('productReference', 'productCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('product[x] allows at most one value')
        return self

class AdverseEventSuspectEntityCausality(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    assessment: fhir_types.CodeableConcept | None = None
    productRelatedness: StrictStr | None = None
    author: fhir_types.Reference | None = None
    method: fhir_types.CodeableConcept | None = None
class AdverseEventSuspectEntity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    instance: fhir_types.Reference
    causality: Annotated[list[AdverseEventSuspectEntityCausality], Field(min_length=1)] | None = None
class AdverseEvent(DomainResourceR4):
    resourceType: Literal['AdverseEvent']
    identifier: fhir_types.Identifier | None = None
    actuality: Literal['actual', 'potential']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    event: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    detected: FHIRDateTime | None = None
    recordedDate: FHIRDateTime | None = None
    resultingCondition: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    seriousness: fhir_types.CodeableConcept | None = None
    severity: fhir_types.CodeableConcept | None = None
    outcome: fhir_types.CodeableConcept | None = None
    recorder: fhir_types.Reference | None = None
    contributor: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    suspectEntity: Annotated[list[AdverseEventSuspectEntity], Field(min_length=1)] | None = None
    subjectMedicalHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    referenceDocument: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    study: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class AllergyIntoleranceReaction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    substance: fhir_types.CodeableConcept | None = None
    manifestation: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)]
    description: StrictStr | None = None
    onset: FHIRDateTime | None = None
    severity: Literal['mild', 'moderate', 'severe'] | None = None
    exposureRoute: fhir_types.CodeableConcept | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
class AllergyIntolerance(DomainResourceR4):
    resourceType: Literal['AllergyIntolerance']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    clinicalStatus: fhir_types.CodeableConcept | None = None
    verificationStatus: fhir_types.CodeableConcept | None = None
    type: Literal['allergy', 'intolerance'] | None = None
    category: Annotated[list[Literal['biologic', 'environment', 'food', 'medication']], Field(min_length=1)] | None = None
    criticality: Literal['high', 'low', 'unable-to-assess'] | None = None
    code: fhir_types.CodeableConcept | None = None
    patient: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    onsetDateTime: FHIRDateTime | None = None
    onsetAge: fhir_types.Age | None = None
    onsetPeriod: fhir_types.Period | None = None
    onsetRange: fhir_types.Range | None = None
    onsetString: StrictStr | None = None
    recordedDate: FHIRDateTime | None = None
    recorder: fhir_types.Reference | None = None
    asserter: fhir_types.Reference | None = None
    lastOccurrence: FHIRDateTime | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    reaction: Annotated[list[AllergyIntoleranceReaction], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'AllergyIntolerance':
        _present = sum(1 for _f in ('onsetDateTime', 'onsetAge', 'onsetPeriod', 'onsetRange', 'onsetString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('onset[x] allows at most one value')
        return self

class AppointmentParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    actor: fhir_types.Reference | None = None
    required: Literal['information-only', 'optional', 'required'] | None = None
    status: Literal['accepted', 'declined', 'needs-action', 'tentative']
    period: fhir_types.Period | None = None
class Appointment(DomainResourceR4):
    resourceType: Literal['Appointment']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['arrived', 'booked', 'cancelled', 'checked-in', 'entered-in-error', 'fulfilled', 'noshow', 'pending', 'proposed', 'waitlist']
    cancelationReason: fhir_types.CodeableConcept | None = None
    serviceCategory: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    serviceType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    appointmentType: fhir_types.CodeableConcept | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    priority: FHIRUnsignedInt | None = None
    description: StrictStr | None = None
    supportingInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    start: FHIRInstant | None = None
    end: FHIRInstant | None = None
    minutesDuration: FHIRPositiveInt | None = None
    slot: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    created: FHIRDateTime | None = None
    comment: StrictStr | None = None
    patientInstruction: StrictStr | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    participant: Annotated[list[AppointmentParticipant], Field(min_length=1)]
    requestedPeriod: Annotated[list[fhir_types.Period], Field(min_length=1)] | None = None

class AppointmentResponse(DomainResourceR4):
    resourceType: Literal['AppointmentResponse']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    appointment: fhir_types.Reference
    start: FHIRInstant | None = None
    end: FHIRInstant | None = None
    participantType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    actor: fhir_types.Reference | None = None
    participantStatus: Literal['accepted', 'declined', 'needs-action', 'tentative']
    comment: StrictStr | None = None

class AuditEventAgentNetwork(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    address: StrictStr | None = None
    type: Literal['1', '2', '3', '4', '5'] | None = None
class AuditEventAgent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    role: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    who: fhir_types.Reference | None = None
    altId: StrictStr | None = None
    name: StrictStr | None = None
    requestor: StrictBool
    location: fhir_types.Reference | None = None
    policy: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    media: fhir_types.Coding | None = None
    network: AuditEventAgentNetwork | None = None
    purposeOfUse: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class AuditEventSource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    site: StrictStr | None = None
    observer: fhir_types.Reference
    type: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
class AuditEventEntityDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: StrictStr
    valueString: StrictStr | None = None
    valueBase64Binary: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'AuditEventEntityDetail':
        _present = sum(1 for _f in ('valueString', 'valueBase64Binary',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class AuditEventEntity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    what: fhir_types.Reference | None = None
    type: fhir_types.Coding | None = None
    role: fhir_types.Coding | None = None
    lifecycle: fhir_types.Coding | None = None
    securityLabel: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    query: StrictStr | None = None
    detail: Annotated[list[AuditEventEntityDetail], Field(min_length=1)] | None = None
class AuditEvent(DomainResourceR4):
    resourceType: Literal['AuditEvent']
    type: fhir_types.Coding
    subtype: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    action: Literal['C', 'D', 'E', 'R', 'U'] | None = None
    period: fhir_types.Period | None = None
    recorded: FHIRInstant
    outcome: Literal['0', '12', '4', '8'] | None = None
    outcomeDesc: StrictStr | None = None
    purposeOfEvent: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    agent: Annotated[list[AuditEventAgent], Field(min_length=1)]
    source: AuditEventSource
    entity: Annotated[list[AuditEventEntity], Field(min_length=1)] | None = None

class Basic(DomainResourceR4):
    resourceType: Literal['Basic']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    subject: fhir_types.Reference | None = None
    created: FHIRDate | None = None
    author: fhir_types.Reference | None = None

class Binary(DomainResourceR4):
    resourceType: Literal['Binary']
    contentType: FHIRCode
    securityContext: fhir_types.Reference | None = None
    data: StrictStr | None = None

class BiologicallyDerivedProductCollection(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    collector: fhir_types.Reference | None = None
    source: fhir_types.Reference | None = None
    collectedDateTime: FHIRDateTime | None = None
    collectedPeriod: fhir_types.Period | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'BiologicallyDerivedProductCollection':
        _present = sum(1 for _f in ('collectedDateTime', 'collectedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('collected[x] allows at most one value')
        return self
class BiologicallyDerivedProductProcessing(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    procedure: fhir_types.CodeableConcept | None = None
    additive: fhir_types.Reference | None = None
    timeDateTime: FHIRDateTime | None = None
    timePeriod: fhir_types.Period | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'BiologicallyDerivedProductProcessing':
        _present = sum(1 for _f in ('timeDateTime', 'timePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('time[x] allows at most one value')
        return self
class BiologicallyDerivedProductManipulation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    timeDateTime: FHIRDateTime | None = None
    timePeriod: fhir_types.Period | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'BiologicallyDerivedProductManipulation':
        _present = sum(1 for _f in ('timeDateTime', 'timePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('time[x] allows at most one value')
        return self
class BiologicallyDerivedProductStorage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    temperature: FHIRDecimal | None = None
    scale: Literal['celsius', 'farenheit', 'kelvin'] | None = None
    duration: fhir_types.Period | None = None
class BiologicallyDerivedProduct(DomainResourceR4):
    resourceType: Literal['BiologicallyDerivedProduct']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    productCategory: Literal['biologicalAgent', 'cells', 'fluid', 'organ', 'tissue'] | None = None
    productCode: fhir_types.CodeableConcept | None = None
    status: Literal['available', 'unavailable'] | None = None
    request: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    quantity: FHIRInteger | None = None
    parent: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    collection: BiologicallyDerivedProductCollection | None = None
    processing: Annotated[list[BiologicallyDerivedProductProcessing], Field(min_length=1)] | None = None
    manipulation: BiologicallyDerivedProductManipulation | None = None
    storage: Annotated[list[BiologicallyDerivedProductStorage], Field(min_length=1)] | None = None

class BodyStructure(DomainResourceR4):
    resourceType: Literal['BodyStructure']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    morphology: fhir_types.CodeableConcept | None = None
    location: fhir_types.CodeableConcept | None = None
    locationQualifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    image: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None
    patient: fhir_types.Reference

class BundleLink(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    relation: StrictStr
    url: StrictStr
class BundleEntrySearch(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['include', 'match', 'outcome'] | None = None
    score: FHIRDecimal | None = None
class BundleEntryRequest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    method: Literal['DELETE', 'GET', 'HEAD', 'PATCH', 'POST', 'PUT']
    url: StrictStr
    ifNoneMatch: StrictStr | None = None
    ifModifiedSince: FHIRInstant | None = None
    ifMatch: StrictStr | None = None
    ifNoneExist: StrictStr | None = None
class BundleEntryResponse(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    status: StrictStr
    location: StrictStr | None = None
    etag: StrictStr | None = None
    lastModified: FHIRInstant | None = None
    outcome: dict[str, Any] | None = None
class BundleEntry(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    link: Annotated[list[BundleLink], Field(min_length=1)] | None = None
    fullUrl: StrictStr | None = None
    resource: dict[str, Any] | None = None
    search: BundleEntrySearch | None = None
    request: BundleEntryRequest | None = None
    response: BundleEntryResponse | None = None
class Bundle(DomainResourceR4):
    resourceType: Literal['Bundle']
    identifier: fhir_types.Identifier | None = None
    type: Literal['batch', 'batch-response', 'collection', 'document', 'history', 'message', 'searchset', 'transaction', 'transaction-response']
    timestamp: FHIRInstant | None = None
    total: FHIRUnsignedInt | None = None
    link: Annotated[list[BundleLink], Field(min_length=1)] | None = None
    entry: Annotated[list[BundleEntry], Field(min_length=1)] | None = None
    signature: fhir_types.Signature | None = None

class CapabilityStatementSoftware(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    version: StrictStr | None = None
    releaseDate: FHIRDateTime | None = None
class CapabilityStatementImplementation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr
    url: StrictStr | None = None
    custodian: fhir_types.Reference | None = None
class CapabilityStatementRestSecurity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    cors: StrictBool | None = None
    service: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    description: StrictStr | None = None
class CapabilityStatementRestResourceInteraction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Literal['create', 'delete', 'history-instance', 'history-type', 'patch', 'read', 'search-type', 'update', 'vread']
    documentation: StrictStr | None = None
class CapabilityStatementRestResourceSearchParam(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    definition: StrictStr | None = None
    type: Literal['composite', 'date', 'number', 'quantity', 'reference', 'special', 'string', 'token', 'uri']
    documentation: StrictStr | None = None
class CapabilityStatementRestResourceOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    definition: StrictStr
    documentation: StrictStr | None = None
class CapabilityStatementRestResource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: FHIRCode
    profile: StrictStr | None = None
    supportedProfile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    documentation: StrictStr | None = None
    interaction: Annotated[list[CapabilityStatementRestResourceInteraction], Field(min_length=1)] | None = None
    versioning: Literal['no-version', 'versioned', 'versioned-update'] | None = None
    readHistory: StrictBool | None = None
    updateCreate: StrictBool | None = None
    conditionalCreate: StrictBool | None = None
    conditionalRead: Literal['full-support', 'modified-since', 'not-match', 'not-supported'] | None = None
    conditionalUpdate: StrictBool | None = None
    conditionalDelete: Literal['multiple', 'not-supported', 'single'] | None = None
    referencePolicy: Annotated[list[Literal['enforced', 'literal', 'local', 'logical', 'resolves']], Field(min_length=1)] | None = None
    searchInclude: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    searchRevInclude: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    searchParam: Annotated[list[CapabilityStatementRestResourceSearchParam], Field(min_length=1)] | None = None
    operation: Annotated[list[CapabilityStatementRestResourceOperation], Field(min_length=1)] | None = None
class CapabilityStatementRestInteraction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Literal['batch', 'history-system', 'search-system', 'transaction']
    documentation: StrictStr | None = None
class CapabilityStatementRest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['client', 'server']
    documentation: StrictStr | None = None
    security: CapabilityStatementRestSecurity | None = None
    resource: Annotated[list[CapabilityStatementRestResource], Field(min_length=1)] | None = None
    interaction: Annotated[list[CapabilityStatementRestInteraction], Field(min_length=1)] | None = None
    searchParam: Annotated[list[CapabilityStatementRestResourceSearchParam], Field(min_length=1)] | None = None
    operation: Annotated[list[CapabilityStatementRestResourceOperation], Field(min_length=1)] | None = None
    compartment: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class CapabilityStatementMessagingEndpoint(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    protocol: fhir_types.Coding
    address: StrictStr
class CapabilityStatementMessagingSupportedMessage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['receiver', 'sender']
    definition: StrictStr
class CapabilityStatementMessaging(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    endpoint: Annotated[list[CapabilityStatementMessagingEndpoint], Field(min_length=1)] | None = None
    reliableCache: FHIRUnsignedInt | None = None
    documentation: StrictStr | None = None
    supportedMessage: Annotated[list[CapabilityStatementMessagingSupportedMessage], Field(min_length=1)] | None = None
class CapabilityStatementDocument(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['consumer', 'producer']
    documentation: StrictStr | None = None
    profile: StrictStr
class CapabilityStatement(DomainResourceR4):
    resourceType: Literal['CapabilityStatement']
    url: StrictStr | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    kind: Literal['capability', 'instance', 'requirements']
    instantiates: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    imports: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    software: CapabilityStatementSoftware | None = None
    implementation: CapabilityStatementImplementation | None = None
    fhirVersion: Literal['0.0.80', '0.0.81', '0.0.82', '0.01', '0.05', '0.06', '0.11', '0.4.0', '0.5.0', '1.0.0', '1.0.1', '1.0.2', '1.1.0', '1.4.0', '1.6.0', '1.8.0', '3.0.0', '3.0.1', '3.3.0', '3.5.0', '4.0.0', '4.0.1']
    format: Annotated[list[FHIRCode], Field(min_length=1)]
    patchFormat: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    implementationGuide: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    rest: Annotated[list[CapabilityStatementRest], Field(min_length=1)] | None = None
    messaging: Annotated[list[CapabilityStatementMessaging], Field(min_length=1)] | None = None
    document: Annotated[list[CapabilityStatementDocument], Field(min_length=1)] | None = None

class CarePlanActivityDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    kind: Literal['Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'Task', 'VisionPrescription'] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    goal: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['cancelled', 'completed', 'entered-in-error', 'in-progress', 'not-started', 'on-hold', 'scheduled', 'stopped', 'unknown']
    statusReason: fhir_types.CodeableConcept | None = None
    doNotPerform: StrictBool | None = None
    scheduledTiming: fhir_types.Timing | None = None
    scheduledPeriod: fhir_types.Period | None = None
    scheduledString: StrictStr | None = None
    location: fhir_types.Reference | None = None
    performer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    productCodeableConcept: fhir_types.CodeableConcept | None = None
    productReference: fhir_types.Reference | None = None
    dailyAmount: fhir_types.SimpleQuantity | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    description: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CarePlanActivityDetail':
        _present = sum(1 for _f in ('scheduledTiming', 'scheduledPeriod', 'scheduledString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('scheduled[x] allows at most one value')
        _present = sum(1 for _f in ('productCodeableConcept', 'productReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('product[x] allows at most one value')
        return self
class CarePlanActivity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    outcomeCodeableConcept: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    outcomeReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    progress: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    reference: fhir_types.Reference | None = None
    detail: CarePlanActivityDetail | None = None
class CarePlan(DomainResourceR4):
    resourceType: Literal['CarePlan']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    replaces: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown']
    intent: Literal['option', 'order', 'plan', 'proposal']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    title: StrictStr | None = None
    description: StrictStr | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    period: fhir_types.Period | None = None
    created: FHIRDateTime | None = None
    author: fhir_types.Reference | None = None
    contributor: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    careTeam: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    addresses: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    goal: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    activity: Annotated[list[CarePlanActivity], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class CareTeamParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    role: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    member: fhir_types.Reference | None = None
    onBehalfOf: fhir_types.Reference | None = None
    period: fhir_types.Period | None = None
class CareTeam(DomainResourceR4):
    resourceType: Literal['CareTeam']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'inactive', 'proposed', 'suspended'] | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    period: fhir_types.Period | None = None
    participant: Annotated[list[CareTeamParticipant], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    managingOrganization: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class CatalogEntryRelatedEntry(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    relationtype: Literal['is-replaced-by', 'triggers']
    item: fhir_types.Reference
class CatalogEntry(DomainResourceR4):
    resourceType: Literal['CatalogEntry']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    orderable: StrictBool
    referencedItem: fhir_types.Reference
    additionalIdentifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    classification: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'retired', 'unknown'] | None = None
    validityPeriod: fhir_types.Period | None = None
    validTo: FHIRDateTime | None = None
    lastUpdated: FHIRDateTime | None = None
    additionalCharacteristic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    additionalClassification: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    relatedEntry: Annotated[list[CatalogEntryRelatedEntry], Field(min_length=1)] | None = None

class ChargeItemPerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class ChargeItem(DomainResourceR4):
    resourceType: Literal['ChargeItem']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    definitionUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    definitionCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['aborted', 'billable', 'billed', 'entered-in-error', 'not-billable', 'planned', 'unknown']
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    subject: fhir_types.Reference
    context: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    performer: Annotated[list[ChargeItemPerformer], Field(min_length=1)] | None = None
    performingOrganization: fhir_types.Reference | None = None
    requestingOrganization: fhir_types.Reference | None = None
    costCenter: fhir_types.Reference | None = None
    quantity: fhir_types.Quantity | None = None
    bodysite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    factorOverride: FHIRDecimal | None = None
    priceOverride: fhir_types.Money | None = None
    overrideReason: StrictStr | None = None
    enterer: fhir_types.Reference | None = None
    enteredDate: FHIRDateTime | None = None
    reason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    service: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    productReference: fhir_types.Reference | None = None
    productCodeableConcept: fhir_types.CodeableConcept | None = None
    account: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    supportingInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ChargeItem':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        _present = sum(1 for _f in ('productReference', 'productCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('product[x] allows at most one value')
        return self

class ChargeItemDefinitionApplicability(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    language: StrictStr | None = None
    expression: StrictStr | None = None
class ChargeItemDefinitionPropertyGroupPriceComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['base', 'deduction', 'discount', 'informational', 'surcharge', 'tax']
    code: fhir_types.CodeableConcept | None = None
    factor: FHIRDecimal | None = None
    amount: fhir_types.Money | None = None
class ChargeItemDefinitionPropertyGroup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    applicability: Annotated[list[ChargeItemDefinitionApplicability], Field(min_length=1)] | None = None
    priceComponent: Annotated[list[ChargeItemDefinitionPropertyGroupPriceComponent], Field(min_length=1)] | None = None
class ChargeItemDefinition(DomainResourceR4):
    resourceType: Literal['ChargeItemDefinition']
    url: StrictStr
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    title: StrictStr | None = None
    derivedFromUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    partOf: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    replaces: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    code: fhir_types.CodeableConcept | None = None
    instance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    applicability: Annotated[list[ChargeItemDefinitionApplicability], Field(min_length=1)] | None = None
    propertyGroup: Annotated[list[ChargeItemDefinitionPropertyGroup], Field(min_length=1)] | None = None

class ClaimRelated(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    claim: fhir_types.Reference | None = None
    relationship: fhir_types.CodeableConcept | None = None
    reference: fhir_types.Identifier | None = None
class ClaimPayee(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    party: fhir_types.Reference | None = None
class ClaimCareTeam(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    provider: fhir_types.Reference
    responsible: StrictBool | None = None
    role: fhir_types.CodeableConcept | None = None
    qualification: fhir_types.CodeableConcept | None = None
class ClaimSupportingInfo(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    category: fhir_types.CodeableConcept
    code: fhir_types.CodeableConcept | None = None
    timingDate: FHIRDate | None = None
    timingPeriod: fhir_types.Period | None = None
    valueBoolean: StrictBool | None = None
    valueString: StrictStr | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueReference: fhir_types.Reference | None = None
    reason: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimSupportingInfo':
        _present = sum(1 for _f in ('timingDate', 'timingPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        _present = sum(1 for _f in ('valueBoolean', 'valueString', 'valueQuantity', 'valueAttachment', 'valueReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class ClaimDiagnosis(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    diagnosisCodeableConcept: fhir_types.CodeableConcept | None = None
    diagnosisReference: fhir_types.Reference | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    onAdmission: fhir_types.CodeableConcept | None = None
    packageCode: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimDiagnosis':
        _present = sum(1 for _f in ('diagnosisCodeableConcept', 'diagnosisReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('diagnosis[x] requires exactly one value')
        return self
class ClaimProcedure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    date: FHIRDateTime | None = None
    procedureCodeableConcept: fhir_types.CodeableConcept | None = None
    procedureReference: fhir_types.Reference | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimProcedure':
        _present = sum(1 for _f in ('procedureCodeableConcept', 'procedureReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('procedure[x] requires exactly one value')
        return self
class ClaimInsurance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    focal: StrictBool
    identifier: fhir_types.Identifier | None = None
    coverage: fhir_types.Reference
    businessArrangement: StrictStr | None = None
    preAuthRef: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    claimResponse: fhir_types.Reference | None = None
class ClaimAccident(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    date: FHIRDate
    type: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimAccident':
        _present = sum(1 for _f in ('locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class ClaimItemDetailSubDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class ClaimItemDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    subDetail: Annotated[list[ClaimItemDetailSubDetail], Field(min_length=1)] | None = None
class ClaimItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    careTeamSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    diagnosisSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    procedureSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    informationSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    locationCodeableConcept: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    subSite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    encounter: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    detail: Annotated[list[ClaimItemDetail], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimItem':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        _present = sum(1 for _f in ('locationCodeableConcept', 'locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class Claim(DomainResourceR4):
    resourceType: Literal['Claim']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    type: fhir_types.CodeableConcept
    subType: fhir_types.CodeableConcept | None = None
    use: Literal['claim', 'preauthorization', 'predetermination']
    patient: fhir_types.Reference
    billablePeriod: fhir_types.Period | None = None
    created: FHIRDateTime
    enterer: fhir_types.Reference | None = None
    insurer: fhir_types.Reference | None = None
    provider: fhir_types.Reference
    priority: fhir_types.CodeableConcept
    fundsReserve: fhir_types.CodeableConcept | None = None
    related: Annotated[list[ClaimRelated], Field(min_length=1)] | None = None
    prescription: fhir_types.Reference | None = None
    originalPrescription: fhir_types.Reference | None = None
    payee: ClaimPayee | None = None
    referral: fhir_types.Reference | None = None
    facility: fhir_types.Reference | None = None
    careTeam: Annotated[list[ClaimCareTeam], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[ClaimSupportingInfo], Field(min_length=1)] | None = None
    diagnosis: Annotated[list[ClaimDiagnosis], Field(min_length=1)] | None = None
    procedure: Annotated[list[ClaimProcedure], Field(min_length=1)] | None = None
    insurance: Annotated[list[ClaimInsurance], Field(min_length=1)]
    accident: ClaimAccident | None = None
    item: Annotated[list[ClaimItem], Field(min_length=1)] | None = None
    total: fhir_types.Money | None = None

class ClaimResponseItemAdjudication(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    reason: fhir_types.CodeableConcept | None = None
    amount: fhir_types.Money | None = None
    value: FHIRDecimal | None = None
class ClaimResponseItemDetailSubDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    subDetailSequence: FHIRPositiveInt
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)] | None = None
class ClaimResponseItemDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    detailSequence: FHIRPositiveInt
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)]
    subDetail: Annotated[list[ClaimResponseItemDetailSubDetail], Field(min_length=1)] | None = None
class ClaimResponseItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemSequence: FHIRPositiveInt
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)]
    detail: Annotated[list[ClaimResponseItemDetail], Field(min_length=1)] | None = None
class ClaimResponseAddItemDetailSubDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)]
class ClaimResponseAddItemDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)]
    subDetail: Annotated[list[ClaimResponseAddItemDetailSubDetail], Field(min_length=1)] | None = None
class ClaimResponseAddItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    detailSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    subdetailSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    provider: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    locationCodeableConcept: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    subSite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)]
    detail: Annotated[list[ClaimResponseAddItemDetail], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClaimResponseAddItem':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        _present = sum(1 for _f in ('locationCodeableConcept', 'locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class ClaimResponseTotal(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    amount: fhir_types.Money
class ClaimResponsePayment(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    adjustment: fhir_types.Money | None = None
    adjustmentReason: fhir_types.CodeableConcept | None = None
    date: FHIRDate | None = None
    amount: fhir_types.Money
    identifier: fhir_types.Identifier | None = None
class ClaimResponseProcessNote(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    number: FHIRPositiveInt | None = None
    type: Literal['display', 'print', 'printoper'] | None = None
    text: StrictStr
    language: fhir_types.CodeableConcept | None = None
class ClaimResponseInsurance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    focal: StrictBool
    coverage: fhir_types.Reference
    businessArrangement: StrictStr | None = None
    claimResponse: fhir_types.Reference | None = None
class ClaimResponseError(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemSequence: FHIRPositiveInt | None = None
    detailSequence: FHIRPositiveInt | None = None
    subDetailSequence: FHIRPositiveInt | None = None
    code: fhir_types.CodeableConcept
class ClaimResponse(DomainResourceR4):
    resourceType: Literal['ClaimResponse']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    type: fhir_types.CodeableConcept
    subType: fhir_types.CodeableConcept | None = None
    use: Literal['claim', 'preauthorization', 'predetermination']
    patient: fhir_types.Reference
    created: FHIRDateTime
    insurer: fhir_types.Reference
    requestor: fhir_types.Reference | None = None
    request: fhir_types.Reference | None = None
    outcome: Literal['complete', 'error', 'partial', 'queued']
    disposition: StrictStr | None = None
    preAuthRef: StrictStr | None = None
    preAuthPeriod: fhir_types.Period | None = None
    payeeType: fhir_types.CodeableConcept | None = None
    item: Annotated[list[ClaimResponseItem], Field(min_length=1)] | None = None
    addItem: Annotated[list[ClaimResponseAddItem], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ClaimResponseItemAdjudication], Field(min_length=1)] | None = None
    total: Annotated[list[ClaimResponseTotal], Field(min_length=1)] | None = None
    payment: ClaimResponsePayment | None = None
    fundsReserve: fhir_types.CodeableConcept | None = None
    formCode: fhir_types.CodeableConcept | None = None
    form: fhir_types.Attachment | None = None
    processNote: Annotated[list[ClaimResponseProcessNote], Field(min_length=1)] | None = None
    communicationRequest: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    insurance: Annotated[list[ClaimResponseInsurance], Field(min_length=1)] | None = None
    error: Annotated[list[ClaimResponseError], Field(min_length=1)] | None = None

class ClinicalImpressionInvestigation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    item: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class ClinicalImpressionFinding(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None
    itemReference: fhir_types.Reference | None = None
    basis: StrictStr | None = None
class ClinicalImpression(DomainResourceR4):
    resourceType: Literal['ClinicalImpression']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress']
    statusReason: fhir_types.CodeableConcept | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    effectiveDateTime: FHIRDateTime | None = None
    effectivePeriod: fhir_types.Period | None = None
    date: FHIRDateTime | None = None
    assessor: fhir_types.Reference | None = None
    previous: fhir_types.Reference | None = None
    problem: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    investigation: Annotated[list[ClinicalImpressionInvestigation], Field(min_length=1)] | None = None
    protocol: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    summary: StrictStr | None = None
    finding: Annotated[list[ClinicalImpressionFinding], Field(min_length=1)] | None = None
    prognosisCodeableConcept: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    prognosisReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ClinicalImpression':
        _present = sum(1 for _f in ('effectiveDateTime', 'effectivePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('effective[x] allows at most one value')
        return self

class CodeSystemFilter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    description: StrictStr | None = None
    operator: Annotated[list[Literal['=', 'descendent-of', 'exists', 'generalizes', 'in', 'is-a', 'is-not-a', 'not-in', 'regex']], Field(min_length=1)]
    value: StrictStr
class CodeSystemProperty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    uri: StrictStr | None = None
    description: StrictStr | None = None
    type: Literal['Coding', 'boolean', 'code', 'dateTime', 'decimal', 'integer', 'string']
class CodeSystemConceptDesignation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    language: FHIRCode | None = None
    use: fhir_types.Coding | None = None
    value: StrictStr
class CodeSystemConceptProperty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    valueCode: FHIRCode | None = None
    valueCoding: fhir_types.Coding | None = None
    valueString: StrictStr | None = None
    valueInteger: FHIRInteger | None = None
    valueBoolean: StrictBool | None = None
    valueDateTime: FHIRDateTime | None = None
    valueDecimal: FHIRDecimal | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CodeSystemConceptProperty':
        _present = sum(1 for _f in ('valueCode', 'valueCoding', 'valueString', 'valueInteger', 'valueBoolean', 'valueDateTime', 'valueDecimal',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class CodeSystemConcept(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    display: StrictStr | None = None
    definition: StrictStr | None = None
    designation: Annotated[list[CodeSystemConceptDesignation], Field(min_length=1)] | None = None
    property: Annotated[list[CodeSystemConceptProperty], Field(min_length=1)] | None = None
    concept: Annotated[list[CodeSystemConcept], Field(min_length=1)] | None = None
class CodeSystem(DomainResourceR4):
    resourceType: Literal['CodeSystem']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    caseSensitive: StrictBool | None = None
    valueSet: StrictStr | None = None
    hierarchyMeaning: Literal['classified-with', 'grouped-by', 'is-a', 'part-of'] | None = None
    compositional: StrictBool | None = None
    versionNeeded: StrictBool | None = None
    content: Literal['complete', 'example', 'fragment', 'not-present', 'supplement']
    supplements: StrictStr | None = None
    count: FHIRUnsignedInt | None = None
    filter: Annotated[list[CodeSystemFilter], Field(min_length=1)] | None = None
    property: Annotated[list[CodeSystemProperty], Field(min_length=1)] | None = None
    concept: Annotated[list[CodeSystemConcept], Field(min_length=1)] | None = None

class CommunicationPayload(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    contentString: StrictStr | None = None
    contentAttachment: fhir_types.Attachment | None = None
    contentReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CommunicationPayload':
        _present = sum(1 for _f in ('contentString', 'contentAttachment', 'contentReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('content[x] requires exactly one value')
        return self
class Communication(DomainResourceR4):
    resourceType: Literal['Communication']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    inResponseTo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress', 'not-done', 'on-hold', 'preparation', 'stopped', 'unknown']
    statusReason: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    medium: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    subject: fhir_types.Reference | None = None
    topic: fhir_types.CodeableConcept | None = None
    about: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    encounter: fhir_types.Reference | None = None
    sent: FHIRDateTime | None = None
    received: FHIRDateTime | None = None
    recipient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    sender: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    payload: Annotated[list[CommunicationPayload], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class CommunicationRequestPayload(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    contentString: StrictStr | None = None
    contentAttachment: fhir_types.Attachment | None = None
    contentReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CommunicationRequestPayload':
        _present = sum(1 for _f in ('contentString', 'contentAttachment', 'contentReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('content[x] requires exactly one value')
        return self
class CommunicationRequest(DomainResourceR4):
    resourceType: Literal['CommunicationRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    replaces: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    groupIdentifier: fhir_types.Identifier | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown']
    statusReason: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    doNotPerform: StrictBool | None = None
    medium: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    subject: fhir_types.Reference | None = None
    about: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    encounter: fhir_types.Reference | None = None
    payload: Annotated[list[CommunicationRequestPayload], Field(min_length=1)] | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    authoredOn: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    recipient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    sender: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CommunicationRequest':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self

class CompartmentDefinitionResource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    param: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    documentation: StrictStr | None = None
class CompartmentDefinition(DomainResourceR4):
    resourceType: Literal['CompartmentDefinition']
    url: StrictStr
    version: StrictStr | None = None
    name: StrictStr
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    code: Literal['Device', 'Encounter', 'Patient', 'Practitioner', 'RelatedPerson']
    search: StrictBool
    resource: Annotated[list[CompartmentDefinitionResource], Field(min_length=1)] | None = None

class CompositionAttester(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['legal', 'official', 'personal', 'professional']
    time: FHIRDateTime | None = None
    party: fhir_types.Reference | None = None
class CompositionRelatesTo(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Literal['appends', 'replaces', 'signs', 'transforms']
    targetIdentifier: fhir_types.Identifier | None = None
    targetReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CompositionRelatesTo':
        _present = sum(1 for _f in ('targetIdentifier', 'targetReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('target[x] requires exactly one value')
        return self
class CompositionEvent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    detail: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class CompositionSection(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    title: StrictStr | None = None
    code: fhir_types.CodeableConcept | None = None
    author: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    focus: fhir_types.Reference | None = None
    text: fhir_types.Narrative | None = None
    mode: Literal['changes', 'snapshot', 'working'] | None = None
    orderedBy: fhir_types.CodeableConcept | None = None
    entry: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    emptyReason: fhir_types.CodeableConcept | None = None
    section: Annotated[list[CompositionSection], Field(min_length=1)] | None = None
class Composition(DomainResourceR4):
    resourceType: Literal['Composition']
    identifier: fhir_types.Identifier | None = None
    status: Literal['amended', 'entered-in-error', 'final', 'preliminary']
    type: fhir_types.CodeableConcept
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    date: FHIRDateTime
    author: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    title: StrictStr
    confidentiality: Literal['L', 'M', 'N', 'R', 'U', 'V'] | None = None
    attester: Annotated[list[CompositionAttester], Field(min_length=1)] | None = None
    custodian: fhir_types.Reference | None = None
    relatesTo: Annotated[list[CompositionRelatesTo], Field(min_length=1)] | None = None
    event: Annotated[list[CompositionEvent], Field(min_length=1)] | None = None
    section: Annotated[list[CompositionSection], Field(min_length=1)] | None = None

class ConceptMapGroupElementTargetDependsOn(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    property: StrictStr
    system: StrictStr | None = None
    value: StrictStr
    display: StrictStr | None = None
class ConceptMapGroupElementTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode | None = None
    display: StrictStr | None = None
    equivalence: Literal['disjoint', 'equal', 'equivalent', 'inexact', 'narrower', 'relatedto', 'specializes', 'subsumes', 'unmatched', 'wider']
    comment: StrictStr | None = None
    dependsOn: Annotated[list[ConceptMapGroupElementTargetDependsOn], Field(min_length=1)] | None = None
    product: Annotated[list[ConceptMapGroupElementTargetDependsOn], Field(min_length=1)] | None = None
class ConceptMapGroupElement(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode | None = None
    display: StrictStr | None = None
    target: Annotated[list[ConceptMapGroupElementTarget], Field(min_length=1)] | None = None
class ConceptMapGroupUnmapped(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    mode: Literal['fixed', 'other-map', 'provided']
    code: FHIRCode | None = None
    display: StrictStr | None = None
    url: StrictStr | None = None
class ConceptMapGroup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    source: StrictStr | None = None
    sourceVersion: StrictStr | None = None
    target: StrictStr | None = None
    targetVersion: StrictStr | None = None
    element: Annotated[list[ConceptMapGroupElement], Field(min_length=1)]
    unmapped: ConceptMapGroupUnmapped | None = None
class ConceptMap(DomainResourceR4):
    resourceType: Literal['ConceptMap']
    url: StrictStr | None = None
    identifier: fhir_types.Identifier | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    sourceUri: StrictStr | None = None
    sourceCanonical: StrictStr | None = None
    targetUri: StrictStr | None = None
    targetCanonical: StrictStr | None = None
    group: Annotated[list[ConceptMapGroup], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ConceptMap':
        _present = sum(1 for _f in ('sourceUri', 'sourceCanonical',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('source[x] allows at most one value')
        _present = sum(1 for _f in ('targetUri', 'targetCanonical',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('target[x] allows at most one value')
        return self

class ConditionStage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    summary: fhir_types.CodeableConcept | None = None
    assessment: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
class ConditionEvidence(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    detail: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class Condition(DomainResourceR4):
    resourceType: Literal['Condition']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    clinicalStatus: fhir_types.CodeableConcept | None = None
    verificationStatus: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    severity: fhir_types.CodeableConcept | None = None
    code: fhir_types.CodeableConcept | None = None
    bodySite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    onsetDateTime: FHIRDateTime | None = None
    onsetAge: fhir_types.Age | None = None
    onsetPeriod: fhir_types.Period | None = None
    onsetRange: fhir_types.Range | None = None
    onsetString: StrictStr | None = None
    abatementDateTime: FHIRDateTime | None = None
    abatementAge: fhir_types.Age | None = None
    abatementPeriod: fhir_types.Period | None = None
    abatementRange: fhir_types.Range | None = None
    abatementString: StrictStr | None = None
    recordedDate: FHIRDateTime | None = None
    recorder: fhir_types.Reference | None = None
    asserter: fhir_types.Reference | None = None
    stage: Annotated[list[ConditionStage], Field(min_length=1)] | None = None
    evidence: Annotated[list[ConditionEvidence], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Condition':
        _present = sum(1 for _f in ('onsetDateTime', 'onsetAge', 'onsetPeriod', 'onsetRange', 'onsetString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('onset[x] allows at most one value')
        _present = sum(1 for _f in ('abatementDateTime', 'abatementAge', 'abatementPeriod', 'abatementRange', 'abatementString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('abatement[x] allows at most one value')
        return self

class ConsentPolicy(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    authority: StrictStr | None = None
    uri: StrictStr | None = None
class ConsentVerification(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    verified: StrictBool
    verifiedWith: fhir_types.Reference | None = None
    verificationDate: FHIRDateTime | None = None
class ConsentProvisionActor(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    role: fhir_types.CodeableConcept
    reference: fhir_types.Reference
class ConsentProvisionData(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    meaning: Literal['authoredby', 'dependents', 'instance', 'related']
    reference: fhir_types.Reference
class ConsentProvision(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['deny', 'permit'] | None = None
    period: fhir_types.Period | None = None
    actor: Annotated[list[ConsentProvisionActor], Field(min_length=1)] | None = None
    action: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    securityLabel: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    purpose: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    class_: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = Field(default=None, alias='class')
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    dataPeriod: fhir_types.Period | None = None
    data: Annotated[list[ConsentProvisionData], Field(min_length=1)] | None = None
    provision: Annotated[list[ConsentProvision], Field(min_length=1)] | None = None
class Consent(DomainResourceR4):
    resourceType: Literal['Consent']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'entered-in-error', 'inactive', 'proposed', 'rejected']
    scope: fhir_types.CodeableConcept
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)]
    patient: fhir_types.Reference | None = None
    dateTime: FHIRDateTime | None = None
    performer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    organization: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    sourceAttachment: fhir_types.Attachment | None = None
    sourceReference: fhir_types.Reference | None = None
    policy: Annotated[list[ConsentPolicy], Field(min_length=1)] | None = None
    policyRule: fhir_types.CodeableConcept | None = None
    verification: Annotated[list[ConsentVerification], Field(min_length=1)] | None = None
    provision: ConsentProvision | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Consent':
        _present = sum(1 for _f in ('sourceAttachment', 'sourceReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('source[x] allows at most one value')
        return self

class ContractContentDefinition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    subType: fhir_types.CodeableConcept | None = None
    publisher: fhir_types.Reference | None = None
    publicationDate: FHIRDateTime | None = None
    publicationStatus: Literal['amended', 'appended', 'cancelled', 'disputed', 'entered-in-error', 'executable', 'executed', 'negotiable', 'offered', 'policy', 'rejected', 'renewed', 'resolved', 'revoked', 'terminated']
    copyright: StrictStr | None = None
class ContractTermSecurityLabel(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    number: Annotated[list[FHIRUnsignedInt], Field(min_length=1)] | None = None
    classification: fhir_types.Coding
    category: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    control: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
class ContractTermOfferParty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    reference: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    role: fhir_types.CodeableConcept
class ContractTermOfferAnswer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    valueBoolean: StrictBool | None = None
    valueDecimal: FHIRDecimal | None = None
    valueInteger: FHIRInteger | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueTime: FHIRTime | None = None
    valueString: StrictStr | None = None
    valueUri: StrictStr | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCoding: fhir_types.Coding | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractTermOfferAnswer':
        _present = sum(1 for _f in ('valueBoolean', 'valueDecimal', 'valueInteger', 'valueDate', 'valueDateTime', 'valueTime', 'valueString', 'valueUri', 'valueAttachment', 'valueCoding', 'valueQuantity', 'valueReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class ContractTermOffer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    party: Annotated[list[ContractTermOfferParty], Field(min_length=1)] | None = None
    topic: fhir_types.Reference | None = None
    type: fhir_types.CodeableConcept | None = None
    decision: fhir_types.CodeableConcept | None = None
    decisionMode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    answer: Annotated[list[ContractTermOfferAnswer], Field(min_length=1)] | None = None
    text: StrictStr | None = None
    linkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    securityLabelNumber: Annotated[list[FHIRUnsignedInt], Field(min_length=1)] | None = None
class ContractTermAssetContext(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    reference: fhir_types.Reference | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    text: StrictStr | None = None
class ContractTermAssetValuedItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    entityCodeableConcept: fhir_types.CodeableConcept | None = None
    entityReference: fhir_types.Reference | None = None
    identifier: fhir_types.Identifier | None = None
    effectiveTime: FHIRDateTime | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    points: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    payment: StrictStr | None = None
    paymentDate: FHIRDateTime | None = None
    responsible: fhir_types.Reference | None = None
    recipient: fhir_types.Reference | None = None
    linkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    securityLabelNumber: Annotated[list[FHIRUnsignedInt], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractTermAssetValuedItem':
        _present = sum(1 for _f in ('entityCodeableConcept', 'entityReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('entity[x] allows at most one value')
        return self
class ContractTermAsset(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    scope: fhir_types.CodeableConcept | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    typeReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    subtype: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    relationship: fhir_types.Coding | None = None
    context: Annotated[list[ContractTermAssetContext], Field(min_length=1)] | None = None
    condition: StrictStr | None = None
    periodType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    period: Annotated[list[fhir_types.Period], Field(min_length=1)] | None = None
    usePeriod: Annotated[list[fhir_types.Period], Field(min_length=1)] | None = None
    text: StrictStr | None = None
    linkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    answer: Annotated[list[ContractTermOfferAnswer], Field(min_length=1)] | None = None
    securityLabelNumber: Annotated[list[FHIRUnsignedInt], Field(min_length=1)] | None = None
    valuedItem: Annotated[list[ContractTermAssetValuedItem], Field(min_length=1)] | None = None
class ContractTermActionSubject(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    reference: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    role: fhir_types.CodeableConcept | None = None
class ContractTermAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    doNotPerform: StrictBool | None = None
    type: fhir_types.CodeableConcept
    subject: Annotated[list[ContractTermActionSubject], Field(min_length=1)] | None = None
    intent: fhir_types.CodeableConcept
    linkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: fhir_types.CodeableConcept
    context: fhir_types.Reference | None = None
    contextLinkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    requester: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    requesterLinkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    performerType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    performerRole: fhir_types.CodeableConcept | None = None
    performer: fhir_types.Reference | None = None
    performerLinkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    reason: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    reasonLinkId: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    securityLabelNumber: Annotated[list[FHIRUnsignedInt], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractTermAction':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self
class ContractTerm(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    issued: FHIRDateTime | None = None
    applies: fhir_types.Period | None = None
    topicCodeableConcept: fhir_types.CodeableConcept | None = None
    topicReference: fhir_types.Reference | None = None
    type: fhir_types.CodeableConcept | None = None
    subType: fhir_types.CodeableConcept | None = None
    text: StrictStr | None = None
    securityLabel: Annotated[list[ContractTermSecurityLabel], Field(min_length=1)] | None = None
    offer: ContractTermOffer
    asset: Annotated[list[ContractTermAsset], Field(min_length=1)] | None = None
    action: Annotated[list[ContractTermAction], Field(min_length=1)] | None = None
    group: Annotated[list[ContractTerm], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractTerm':
        _present = sum(1 for _f in ('topicCodeableConcept', 'topicReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('topic[x] allows at most one value')
        return self
class ContractSigner(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.Coding
    party: fhir_types.Reference
    signature: Annotated[list[fhir_types.Signature], Field(min_length=1)]
class ContractFriendly(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    contentAttachment: fhir_types.Attachment | None = None
    contentReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractFriendly':
        _present = sum(1 for _f in ('contentAttachment', 'contentReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('content[x] requires exactly one value')
        return self
class ContractLegal(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    contentAttachment: fhir_types.Attachment | None = None
    contentReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractLegal':
        _present = sum(1 for _f in ('contentAttachment', 'contentReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('content[x] requires exactly one value')
        return self
class ContractRule(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    contentAttachment: fhir_types.Attachment | None = None
    contentReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ContractRule':
        _present = sum(1 for _f in ('contentAttachment', 'contentReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('content[x] requires exactly one value')
        return self
class Contract(DomainResourceR4):
    resourceType: Literal['Contract']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    url: StrictStr | None = None
    version: StrictStr | None = None
    status: Literal['amended', 'appended', 'cancelled', 'disputed', 'entered-in-error', 'executable', 'executed', 'negotiable', 'offered', 'policy', 'rejected', 'renewed', 'resolved', 'revoked', 'terminated'] | None = None
    legalState: fhir_types.CodeableConcept | None = None
    instantiatesCanonical: fhir_types.Reference | None = None
    instantiatesUri: StrictStr | None = None
    contentDerivative: fhir_types.CodeableConcept | None = None
    issued: FHIRDateTime | None = None
    applies: fhir_types.Period | None = None
    expirationType: fhir_types.CodeableConcept | None = None
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    authority: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    domain: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    site: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    alias: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    author: fhir_types.Reference | None = None
    scope: fhir_types.CodeableConcept | None = None
    topicCodeableConcept: fhir_types.CodeableConcept | None = None
    topicReference: fhir_types.Reference | None = None
    type: fhir_types.CodeableConcept | None = None
    subType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    contentDefinition: ContractContentDefinition | None = None
    term: Annotated[list[ContractTerm], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    relevantHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    signer: Annotated[list[ContractSigner], Field(min_length=1)] | None = None
    friendly: Annotated[list[ContractFriendly], Field(min_length=1)] | None = None
    legal: Annotated[list[ContractLegal], Field(min_length=1)] | None = None
    rule: Annotated[list[ContractRule], Field(min_length=1)] | None = None
    legallyBindingAttachment: fhir_types.Attachment | None = None
    legallyBindingReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Contract':
        _present = sum(1 for _f in ('topicCodeableConcept', 'topicReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('topic[x] allows at most one value')
        _present = sum(1 for _f in ('legallyBindingAttachment', 'legallyBindingReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('legallyBinding[x] allows at most one value')
        return self

class CoverageClass(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    value: StrictStr
    name: StrictStr | None = None
class CoverageCostToBeneficiaryException(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    period: fhir_types.Period | None = None
class CoverageCostToBeneficiary(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    valueQuantity: fhir_types.SimpleQuantity | None = None
    valueMoney: fhir_types.Money | None = None
    exception: Annotated[list[CoverageCostToBeneficiaryException], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CoverageCostToBeneficiary':
        _present = sum(1 for _f in ('valueQuantity', 'valueMoney',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class Coverage(DomainResourceR4):
    resourceType: Literal['Coverage']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    type: fhir_types.CodeableConcept | None = None
    policyHolder: fhir_types.Reference | None = None
    subscriber: fhir_types.Reference | None = None
    subscriberId: StrictStr | None = None
    beneficiary: fhir_types.Reference
    dependent: StrictStr | None = None
    relationship: fhir_types.CodeableConcept | None = None
    period: fhir_types.Period | None = None
    payor: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    class_: Annotated[list[CoverageClass], Field(min_length=1)] | None = Field(default=None, alias='class')
    order: FHIRPositiveInt | None = None
    network: StrictStr | None = None
    costToBeneficiary: Annotated[list[CoverageCostToBeneficiary], Field(min_length=1)] | None = None
    subrogation: StrictBool | None = None
    contract: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class CoverageEligibilityRequestSupportingInfo(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    information: fhir_types.Reference
    appliesToAll: StrictBool | None = None
class CoverageEligibilityRequestInsurance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    focal: StrictBool | None = None
    coverage: fhir_types.Reference
    businessArrangement: StrictStr | None = None
class CoverageEligibilityRequestItemDiagnosis(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    diagnosisCodeableConcept: fhir_types.CodeableConcept | None = None
    diagnosisReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CoverageEligibilityRequestItemDiagnosis':
        _present = sum(1 for _f in ('diagnosisCodeableConcept', 'diagnosisReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('diagnosis[x] allows at most one value')
        return self
class CoverageEligibilityRequestItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    supportingInfoSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept | None = None
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    provider: fhir_types.Reference | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    facility: fhir_types.Reference | None = None
    diagnosis: Annotated[list[CoverageEligibilityRequestItemDiagnosis], Field(min_length=1)] | None = None
    detail: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class CoverageEligibilityRequest(DomainResourceR4):
    resourceType: Literal['CoverageEligibilityRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    priority: fhir_types.CodeableConcept | None = None
    purpose: Annotated[list[Literal['auth-requirements', 'benefits', 'discovery', 'validation']], Field(min_length=1)]
    patient: fhir_types.Reference
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    created: FHIRDateTime
    enterer: fhir_types.Reference | None = None
    provider: fhir_types.Reference | None = None
    insurer: fhir_types.Reference
    facility: fhir_types.Reference | None = None
    supportingInfo: Annotated[list[CoverageEligibilityRequestSupportingInfo], Field(min_length=1)] | None = None
    insurance: Annotated[list[CoverageEligibilityRequestInsurance], Field(min_length=1)] | None = None
    item: Annotated[list[CoverageEligibilityRequestItem], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CoverageEligibilityRequest':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        return self

class CoverageEligibilityResponseInsuranceItemBenefit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    allowedUnsignedInt: FHIRUnsignedInt | None = None
    allowedString: StrictStr | None = None
    allowedMoney: fhir_types.Money | None = None
    usedUnsignedInt: FHIRUnsignedInt | None = None
    usedString: StrictStr | None = None
    usedMoney: fhir_types.Money | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CoverageEligibilityResponseInsuranceItemBenefit':
        _present = sum(1 for _f in ('allowedUnsignedInt', 'allowedString', 'allowedMoney',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('allowed[x] allows at most one value')
        _present = sum(1 for _f in ('usedUnsignedInt', 'usedString', 'usedMoney',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('used[x] allows at most one value')
        return self
class CoverageEligibilityResponseInsuranceItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept | None = None
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    provider: fhir_types.Reference | None = None
    excluded: StrictBool | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    network: fhir_types.CodeableConcept | None = None
    unit: fhir_types.CodeableConcept | None = None
    term: fhir_types.CodeableConcept | None = None
    benefit: Annotated[list[CoverageEligibilityResponseInsuranceItemBenefit], Field(min_length=1)] | None = None
    authorizationRequired: StrictBool | None = None
    authorizationSupporting: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    authorizationUrl: StrictStr | None = None
class CoverageEligibilityResponseInsurance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    coverage: fhir_types.Reference
    inforce: StrictBool | None = None
    benefitPeriod: fhir_types.Period | None = None
    item: Annotated[list[CoverageEligibilityResponseInsuranceItem], Field(min_length=1)] | None = None
class CoverageEligibilityResponseError(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
class CoverageEligibilityResponse(DomainResourceR4):
    resourceType: Literal['CoverageEligibilityResponse']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    purpose: Annotated[list[Literal['auth-requirements', 'benefits', 'discovery', 'validation']], Field(min_length=1)]
    patient: fhir_types.Reference
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    created: FHIRDateTime
    requestor: fhir_types.Reference | None = None
    request: fhir_types.Reference
    outcome: Literal['complete', 'error', 'partial', 'queued']
    disposition: StrictStr | None = None
    insurer: fhir_types.Reference
    insurance: Annotated[list[CoverageEligibilityResponseInsurance], Field(min_length=1)] | None = None
    preAuthRef: StrictStr | None = None
    form: fhir_types.CodeableConcept | None = None
    error: Annotated[list[CoverageEligibilityResponseError], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'CoverageEligibilityResponse':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        return self

class DetectedIssueEvidence(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    detail: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class DetectedIssueMitigation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: fhir_types.CodeableConcept
    date: FHIRDateTime | None = None
    author: fhir_types.Reference | None = None
class DetectedIssue(DomainResourceR4):
    resourceType: Literal['DetectedIssue']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['amended', 'cancelled', 'corrected', 'entered-in-error', 'final', 'preliminary', 'registered', 'unknown']
    code: fhir_types.CodeableConcept | None = None
    severity: Literal['high', 'low', 'moderate'] | None = None
    patient: fhir_types.Reference | None = None
    identifiedDateTime: FHIRDateTime | None = None
    identifiedPeriod: fhir_types.Period | None = None
    author: fhir_types.Reference | None = None
    implicated: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    evidence: Annotated[list[DetectedIssueEvidence], Field(min_length=1)] | None = None
    detail: StrictStr | None = None
    reference: StrictStr | None = None
    mitigation: Annotated[list[DetectedIssueMitigation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DetectedIssue':
        _present = sum(1 for _f in ('identifiedDateTime', 'identifiedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('identified[x] allows at most one value')
        return self

class DeviceUdiCarrier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    deviceIdentifier: StrictStr | None = None
    issuer: StrictStr | None = None
    jurisdiction: StrictStr | None = None
    carrierAIDC: StrictStr | None = None
    carrierHRF: StrictStr | None = None
    entryType: Literal['barcode', 'card', 'manual', 'rfid', 'self-reported', 'unknown'] | None = None
class DeviceDeviceName(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    type: Literal['manufacturer-name', 'model-name', 'other', 'patient-reported-name', 'udi-label-name', 'user-friendly-name']
class DeviceSpecialization(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    systemType: fhir_types.CodeableConcept
    version: StrictStr | None = None
class DeviceVersion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    component: fhir_types.Identifier | None = None
    value: StrictStr
class DeviceProperty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    valueQuantity: Annotated[list[fhir_types.Quantity], Field(min_length=1)] | None = None
    valueCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class Device(DomainResourceR4):
    resourceType: Literal['Device']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    definition: fhir_types.Reference | None = None
    udiCarrier: Annotated[list[DeviceUdiCarrier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'inactive', 'unknown'] | None = None
    statusReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    distinctIdentifier: StrictStr | None = None
    manufacturer: StrictStr | None = None
    manufactureDate: FHIRDateTime | None = None
    expirationDate: FHIRDateTime | None = None
    lotNumber: StrictStr | None = None
    serialNumber: StrictStr | None = None
    deviceName: Annotated[list[DeviceDeviceName], Field(min_length=1)] | None = None
    modelNumber: StrictStr | None = None
    partNumber: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    specialization: Annotated[list[DeviceSpecialization], Field(min_length=1)] | None = None
    version: Annotated[list[DeviceVersion], Field(min_length=1)] | None = None
    property: Annotated[list[DeviceProperty], Field(min_length=1)] | None = None
    patient: fhir_types.Reference | None = None
    owner: fhir_types.Reference | None = None
    contact: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    url: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    safety: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    parent: fhir_types.Reference | None = None

class DeviceDefinitionUdiDeviceIdentifier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    deviceIdentifier: StrictStr
    issuer: StrictStr
    jurisdiction: StrictStr
class DeviceDefinitionDeviceName(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    type: Literal['manufacturer-name', 'model-name', 'other', 'patient-reported-name', 'udi-label-name', 'user-friendly-name']
class DeviceDefinitionSpecialization(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    systemType: StrictStr
    version: StrictStr | None = None
class DeviceDefinitionCapability(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    description: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class DeviceDefinitionProperty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    valueQuantity: Annotated[list[fhir_types.Quantity], Field(min_length=1)] | None = None
    valueCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class DeviceDefinitionMaterial(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    substance: fhir_types.CodeableConcept
    alternate: StrictBool | None = None
    allergenicIndicator: StrictBool | None = None
class DeviceDefinition(DomainResourceR4):
    resourceType: Literal['DeviceDefinition']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    udiDeviceIdentifier: Annotated[list[DeviceDefinitionUdiDeviceIdentifier], Field(min_length=1)] | None = None
    manufacturerString: StrictStr | None = None
    manufacturerReference: fhir_types.Reference | None = None
    deviceName: Annotated[list[DeviceDefinitionDeviceName], Field(min_length=1)] | None = None
    modelNumber: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    specialization: Annotated[list[DeviceDefinitionSpecialization], Field(min_length=1)] | None = None
    version: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    safety: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    shelfLifeStorage: Annotated[list[fhir_types.ProductShelfLife], Field(min_length=1)] | None = None
    physicalCharacteristics: fhir_types.ProdCharacteristic | None = None
    languageCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    capability: Annotated[list[DeviceDefinitionCapability], Field(min_length=1)] | None = None
    property: Annotated[list[DeviceDefinitionProperty], Field(min_length=1)] | None = None
    owner: fhir_types.Reference | None = None
    contact: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    url: StrictStr | None = None
    onlineInformation: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    quantity: fhir_types.Quantity | None = None
    parentDevice: fhir_types.Reference | None = None
    material: Annotated[list[DeviceDefinitionMaterial], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DeviceDefinition':
        _present = sum(1 for _f in ('manufacturerString', 'manufacturerReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('manufacturer[x] allows at most one value')
        return self

class DeviceMetricCalibration(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['gain', 'offset', 'two-point', 'unspecified'] | None = None
    state: Literal['calibrated', 'calibration-required', 'not-calibrated', 'unspecified'] | None = None
    time: FHIRInstant | None = None
class DeviceMetric(DomainResourceR4):
    resourceType: Literal['DeviceMetric']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    unit: fhir_types.CodeableConcept | None = None
    source: fhir_types.Reference | None = None
    parent: fhir_types.Reference | None = None
    operationalStatus: Literal['entered-in-error', 'off', 'on', 'standby'] | None = None
    color: Literal['black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white', 'yellow'] | None = None
    category: Literal['calculation', 'measurement', 'setting', 'unspecified']
    measurementPeriod: fhir_types.Timing | None = None
    calibration: Annotated[list[DeviceMetricCalibration], Field(min_length=1)] | None = None

class DeviceRequestParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueBoolean: StrictBool | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DeviceRequestParameter':
        _present = sum(1 for _f in ('valueCodeableConcept', 'valueQuantity', 'valueRange', 'valueBoolean',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class DeviceRequest(DomainResourceR4):
    resourceType: Literal['DeviceRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    priorRequest: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    groupIdentifier: fhir_types.Identifier | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown'] | None = None
    intent: Literal['directive', 'filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order']
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    codeReference: fhir_types.Reference | None = None
    codeCodeableConcept: fhir_types.CodeableConcept | None = None
    parameter: Annotated[list[DeviceRequestParameter], Field(min_length=1)] | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    authoredOn: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    performerType: fhir_types.CodeableConcept | None = None
    performer: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    insurance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    relevantHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DeviceRequest':
        _present = sum(1 for _f in ('codeReference', 'codeCodeableConcept',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('code[x] requires exactly one value')
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self

class DeviceUseStatement(DomainResourceR4):
    resourceType: Literal['DeviceUseStatement']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['active', 'completed', 'entered-in-error', 'intended', 'on-hold', 'stopped']
    subject: fhir_types.Reference
    derivedFrom: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    timingTiming: fhir_types.Timing | None = None
    timingPeriod: fhir_types.Period | None = None
    timingDateTime: FHIRDateTime | None = None
    recordedOn: FHIRDateTime | None = None
    source: fhir_types.Reference | None = None
    device: fhir_types.Reference
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DeviceUseStatement':
        _present = sum(1 for _f in ('timingTiming', 'timingPeriod', 'timingDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        return self

class DiagnosticReportMedia(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    comment: StrictStr | None = None
    link: fhir_types.Reference
class DiagnosticReport(DomainResourceR4):
    resourceType: Literal['DiagnosticReport']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['amended', 'appended', 'cancelled', 'corrected', 'entered-in-error', 'final', 'partial', 'preliminary', 'registered', 'unknown']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    effectiveDateTime: FHIRDateTime | None = None
    effectivePeriod: fhir_types.Period | None = None
    issued: FHIRInstant | None = None
    performer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    resultsInterpreter: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    specimen: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    result: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    imagingStudy: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    media: Annotated[list[DiagnosticReportMedia], Field(min_length=1)] | None = None
    conclusion: StrictStr | None = None
    conclusionCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    presentedForm: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DiagnosticReport':
        _present = sum(1 for _f in ('effectiveDateTime', 'effectivePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('effective[x] allows at most one value')
        return self

class DocumentManifestRelated(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    ref: fhir_types.Reference | None = None
class DocumentManifest(DomainResourceR4):
    resourceType: Literal['DocumentManifest']
    masterIdentifier: fhir_types.Identifier | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['current', 'entered-in-error', 'superseded']
    type: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    created: FHIRDateTime | None = None
    author: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    recipient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    source: StrictStr | None = None
    description: StrictStr | None = None
    content: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    related: Annotated[list[DocumentManifestRelated], Field(min_length=1)] | None = None

class DocumentReferenceRelatesTo(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Literal['appends', 'replaces', 'signs', 'transforms']
    target: fhir_types.Reference
class DocumentReferenceContent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    attachment: fhir_types.Attachment
    format: fhir_types.Coding | None = None
class DocumentReferenceContext(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    encounter: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    event: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    facilityType: fhir_types.CodeableConcept | None = None
    practiceSetting: fhir_types.CodeableConcept | None = None
    sourcePatientInfo: fhir_types.Reference | None = None
    related: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class DocumentReference(DomainResourceR4):
    resourceType: Literal['DocumentReference']
    masterIdentifier: fhir_types.Identifier | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['current', 'entered-in-error', 'superseded']
    docStatus: Literal['amended', 'entered-in-error', 'final', 'preliminary'] | None = None
    type: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    subject: fhir_types.Reference | None = None
    date: FHIRInstant | None = None
    author: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    authenticator: fhir_types.Reference | None = None
    custodian: fhir_types.Reference | None = None
    relatesTo: Annotated[list[DocumentReferenceRelatesTo], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    securityLabel: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    content: Annotated[list[DocumentReferenceContent], Field(min_length=1)]
    context: DocumentReferenceContext | None = None

class EffectEvidenceSynthesisSampleSize(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    numberOfStudies: FHIRInteger | None = None
    numberOfParticipants: FHIRInteger | None = None
class EffectEvidenceSynthesisResultsByExposure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    exposureState: Literal['exposure', 'exposure-alternative'] | None = None
    variantState: fhir_types.CodeableConcept | None = None
    riskEvidenceSynthesis: fhir_types.Reference
class EffectEvidenceSynthesisEffectEstimatePrecisionEstimate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    level: FHIRDecimal | None = None
    from_: FHIRDecimal | None = Field(default=None, alias='from')
    to: FHIRDecimal | None = None
class EffectEvidenceSynthesisEffectEstimate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    variantState: fhir_types.CodeableConcept | None = None
    value: FHIRDecimal | None = None
    unitOfMeasure: fhir_types.CodeableConcept | None = None
    precisionEstimate: Annotated[list[EffectEvidenceSynthesisEffectEstimatePrecisionEstimate], Field(min_length=1)] | None = None
class EffectEvidenceSynthesisCertaintyCertaintySubcomponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    rating: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
class EffectEvidenceSynthesisCertainty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    rating: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    certaintySubcomponent: Annotated[list[EffectEvidenceSynthesisCertaintyCertaintySubcomponent], Field(min_length=1)] | None = None
class EffectEvidenceSynthesis(DomainResourceR4):
    resourceType: Literal['EffectEvidenceSynthesis']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    synthesisType: fhir_types.CodeableConcept | None = None
    studyType: fhir_types.CodeableConcept | None = None
    population: fhir_types.Reference
    exposure: fhir_types.Reference
    exposureAlternative: fhir_types.Reference
    outcome: fhir_types.Reference
    sampleSize: EffectEvidenceSynthesisSampleSize | None = None
    resultsByExposure: Annotated[list[EffectEvidenceSynthesisResultsByExposure], Field(min_length=1)] | None = None
    effectEstimate: Annotated[list[EffectEvidenceSynthesisEffectEstimate], Field(min_length=1)] | None = None
    certainty: Annotated[list[EffectEvidenceSynthesisCertainty], Field(min_length=1)] | None = None

class EncounterStatusHistory(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    status: Literal['arrived', 'cancelled', 'entered-in-error', 'finished', 'in-progress', 'onleave', 'planned', 'triaged', 'unknown']
    period: fhir_types.Period
class EncounterClassHistory(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    class_: fhir_types.Coding = Field(alias='class')
    period: fhir_types.Period
class EncounterParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    individual: fhir_types.Reference | None = None
class EncounterDiagnosis(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    condition: fhir_types.Reference
    use: fhir_types.CodeableConcept | None = None
    rank: FHIRPositiveInt | None = None
class EncounterHospitalization(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    preAdmissionIdentifier: fhir_types.Identifier | None = None
    origin: fhir_types.Reference | None = None
    admitSource: fhir_types.CodeableConcept | None = None
    reAdmission: fhir_types.CodeableConcept | None = None
    dietPreference: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialCourtesy: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialArrangement: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    destination: fhir_types.Reference | None = None
    dischargeDisposition: fhir_types.CodeableConcept | None = None
class EncounterLocation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    location: fhir_types.Reference
    status: Literal['active', 'completed', 'planned', 'reserved'] | None = None
    physicalType: fhir_types.CodeableConcept | None = None
    period: fhir_types.Period | None = None
class Encounter(DomainResourceR4):
    resourceType: Literal['Encounter']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['arrived', 'cancelled', 'entered-in-error', 'finished', 'in-progress', 'onleave', 'planned', 'triaged', 'unknown']
    statusHistory: Annotated[list[EncounterStatusHistory], Field(min_length=1)] | None = None
    class_: fhir_types.Coding = Field(alias='class')
    classHistory: Annotated[list[EncounterClassHistory], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    serviceType: fhir_types.CodeableConcept | None = None
    priority: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    episodeOfCare: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    participant: Annotated[list[EncounterParticipant], Field(min_length=1)] | None = None
    appointment: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    length: fhir_types.Duration | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    diagnosis: Annotated[list[EncounterDiagnosis], Field(min_length=1)] | None = None
    account: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    hospitalization: EncounterHospitalization | None = None
    location: Annotated[list[EncounterLocation], Field(min_length=1)] | None = None
    serviceProvider: fhir_types.Reference | None = None
    partOf: fhir_types.Reference | None = None

class Endpoint(DomainResourceR4):
    resourceType: Literal['Endpoint']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'error', 'off', 'suspended', 'test']
    connectionType: fhir_types.Coding
    name: StrictStr | None = None
    managingOrganization: fhir_types.Reference | None = None
    contact: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    payloadType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)]
    payloadMimeType: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    address: StrictStr
    header: Annotated[list[StrictStr], Field(min_length=1)] | None = None

class EnrollmentRequest(DomainResourceR4):
    resourceType: Literal['EnrollmentRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error'] | None = None
    created: FHIRDateTime | None = None
    insurer: fhir_types.Reference | None = None
    provider: fhir_types.Reference | None = None
    candidate: fhir_types.Reference | None = None
    coverage: fhir_types.Reference | None = None

class EnrollmentResponse(DomainResourceR4):
    resourceType: Literal['EnrollmentResponse']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error'] | None = None
    request: fhir_types.Reference | None = None
    outcome: Literal['complete', 'error', 'partial', 'queued'] | None = None
    disposition: StrictStr | None = None
    created: FHIRDateTime | None = None
    organization: fhir_types.Reference | None = None
    requestProvider: fhir_types.Reference | None = None

class EpisodeOfCareStatusHistory(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'entered-in-error', 'finished', 'onhold', 'planned', 'waitlist']
    period: fhir_types.Period
class EpisodeOfCareDiagnosis(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    condition: fhir_types.Reference
    role: fhir_types.CodeableConcept | None = None
    rank: FHIRPositiveInt | None = None
class EpisodeOfCare(DomainResourceR4):
    resourceType: Literal['EpisodeOfCare']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'entered-in-error', 'finished', 'onhold', 'planned', 'waitlist']
    statusHistory: Annotated[list[EpisodeOfCareStatusHistory], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    diagnosis: Annotated[list[EpisodeOfCareDiagnosis], Field(min_length=1)] | None = None
    patient: fhir_types.Reference
    managingOrganization: fhir_types.Reference | None = None
    period: fhir_types.Period | None = None
    referralRequest: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    careManager: fhir_types.Reference | None = None
    team: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    account: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class EventDefinition(DomainResourceR4):
    resourceType: Literal['EventDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    trigger: Annotated[list[fhir_types.TriggerDefinition], Field(min_length=1)]

    @model_validator(mode='after')
    def _check_choices(self) -> 'EventDefinition':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class Evidence(DomainResourceR4):
    resourceType: Literal['Evidence']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    shortTitle: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    exposureBackground: fhir_types.Reference
    exposureVariant: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    outcome: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class EvidenceVariableCharacteristic(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    definitionReference: fhir_types.Reference | None = None
    definitionCanonical: StrictStr | None = None
    definitionCodeableConcept: fhir_types.CodeableConcept | None = None
    definitionExpression: fhir_types.Expression | None = None
    definitionDataRequirement: fhir_types.DataRequirement | None = None
    definitionTriggerDefinition: fhir_types.TriggerDefinition | None = None
    usageContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    exclude: StrictBool | None = None
    participantEffectiveDateTime: FHIRDateTime | None = None
    participantEffectivePeriod: fhir_types.Period | None = None
    participantEffectiveDuration: fhir_types.Duration | None = None
    participantEffectiveTiming: fhir_types.Timing | None = None
    timeFromStart: fhir_types.Duration | None = None
    groupMeasure: Literal['mean', 'mean-of-mean', 'mean-of-median', 'median', 'median-of-mean', 'median-of-median'] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'EvidenceVariableCharacteristic':
        _present = sum(1 for _f in ('definitionReference', 'definitionCanonical', 'definitionCodeableConcept', 'definitionExpression', 'definitionDataRequirement', 'definitionTriggerDefinition',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('definition[x] requires exactly one value')
        _present = sum(1 for _f in ('participantEffectiveDateTime', 'participantEffectivePeriod', 'participantEffectiveDuration', 'participantEffectiveTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('participantEffective[x] allows at most one value')
        return self
class EvidenceVariable(DomainResourceR4):
    resourceType: Literal['EvidenceVariable']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    shortTitle: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    type: Literal['continuous', 'descriptive', 'dichotomous'] | None = None
    characteristic: Annotated[list[EvidenceVariableCharacteristic], Field(min_length=1)]

class ExampleScenarioActor(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    actorId: StrictStr
    type: Literal['entity', 'person']
    name: StrictStr | None = None
    description: StrictStr | None = None
class ExampleScenarioInstanceVersion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    versionId: StrictStr
    description: StrictStr
class ExampleScenarioInstanceContainedInstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    resourceId: StrictStr
    versionId: StrictStr | None = None
class ExampleScenarioInstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    resourceId: StrictStr
    resourceType: FHIRCode
    name: StrictStr | None = None
    description: StrictStr | None = None
    version: Annotated[list[ExampleScenarioInstanceVersion], Field(min_length=1)] | None = None
    containedInstance: Annotated[list[ExampleScenarioInstanceContainedInstance], Field(min_length=1)] | None = None
class ExampleScenarioProcessStepOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    number: StrictStr
    type: StrictStr | None = None
    name: StrictStr | None = None
    initiator: StrictStr | None = None
    receiver: StrictStr | None = None
    description: StrictStr | None = None
    initiatorActive: StrictBool | None = None
    receiverActive: StrictBool | None = None
    request: ExampleScenarioInstanceContainedInstance | None = None
    response: ExampleScenarioInstanceContainedInstance | None = None
class ExampleScenarioProcessStepAlternative(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    title: StrictStr
    description: StrictStr | None = None
    step: Annotated[list[ExampleScenarioProcessStep], Field(min_length=1)] | None = None
class ExampleScenarioProcessStep(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    process: Annotated[list[ExampleScenarioProcess], Field(min_length=1)] | None = None
    pause: StrictBool | None = None
    operation: ExampleScenarioProcessStepOperation | None = None
    alternative: Annotated[list[ExampleScenarioProcessStepAlternative], Field(min_length=1)] | None = None
class ExampleScenarioProcess(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    title: StrictStr
    description: StrictStr | None = None
    preConditions: StrictStr | None = None
    postConditions: StrictStr | None = None
    step: Annotated[list[ExampleScenarioProcessStep], Field(min_length=1)] | None = None
class ExampleScenario(DomainResourceR4):
    resourceType: Literal['ExampleScenario']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    purpose: StrictStr | None = None
    actor: Annotated[list[ExampleScenarioActor], Field(min_length=1)] | None = None
    instance: Annotated[list[ExampleScenarioInstance], Field(min_length=1)] | None = None
    process: Annotated[list[ExampleScenarioProcess], Field(min_length=1)] | None = None
    workflow: Annotated[list[StrictStr], Field(min_length=1)] | None = None

class ExplanationOfBenefitRelated(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    claim: fhir_types.Reference | None = None
    relationship: fhir_types.CodeableConcept | None = None
    reference: fhir_types.Identifier | None = None
class ExplanationOfBenefitPayee(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    party: fhir_types.Reference | None = None
class ExplanationOfBenefitCareTeam(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    provider: fhir_types.Reference
    responsible: StrictBool | None = None
    role: fhir_types.CodeableConcept | None = None
    qualification: fhir_types.CodeableConcept | None = None
class ExplanationOfBenefitSupportingInfo(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    category: fhir_types.CodeableConcept
    code: fhir_types.CodeableConcept | None = None
    timingDate: FHIRDate | None = None
    timingPeriod: fhir_types.Period | None = None
    valueBoolean: StrictBool | None = None
    valueString: StrictStr | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueReference: fhir_types.Reference | None = None
    reason: fhir_types.Coding | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitSupportingInfo':
        _present = sum(1 for _f in ('timingDate', 'timingPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        _present = sum(1 for _f in ('valueBoolean', 'valueString', 'valueQuantity', 'valueAttachment', 'valueReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class ExplanationOfBenefitDiagnosis(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    diagnosisCodeableConcept: fhir_types.CodeableConcept | None = None
    diagnosisReference: fhir_types.Reference | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    onAdmission: fhir_types.CodeableConcept | None = None
    packageCode: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitDiagnosis':
        _present = sum(1 for _f in ('diagnosisCodeableConcept', 'diagnosisReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('diagnosis[x] requires exactly one value')
        return self
class ExplanationOfBenefitProcedure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    date: FHIRDateTime | None = None
    procedureCodeableConcept: fhir_types.CodeableConcept | None = None
    procedureReference: fhir_types.Reference | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitProcedure':
        _present = sum(1 for _f in ('procedureCodeableConcept', 'procedureReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('procedure[x] requires exactly one value')
        return self
class ExplanationOfBenefitInsurance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    focal: StrictBool
    coverage: fhir_types.Reference
    preAuthRef: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class ExplanationOfBenefitAccident(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    date: FHIRDate | None = None
    type: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitAccident':
        _present = sum(1 for _f in ('locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class ExplanationOfBenefitItemAdjudication(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    reason: fhir_types.CodeableConcept | None = None
    amount: fhir_types.Money | None = None
    value: FHIRDecimal | None = None
class ExplanationOfBenefitItemDetailSubDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
class ExplanationOfBenefitItemDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
    subDetail: Annotated[list[ExplanationOfBenefitItemDetailSubDetail], Field(min_length=1)] | None = None
class ExplanationOfBenefitItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt
    careTeamSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    diagnosisSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    procedureSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    informationSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    revenue: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    locationCodeableConcept: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    udi: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    subSite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    encounter: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
    detail: Annotated[list[ExplanationOfBenefitItemDetail], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitItem':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        _present = sum(1 for _f in ('locationCodeableConcept', 'locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class ExplanationOfBenefitAddItemDetailSubDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
class ExplanationOfBenefitAddItemDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
    subDetail: Annotated[list[ExplanationOfBenefitAddItemDetailSubDetail], Field(min_length=1)] | None = None
class ExplanationOfBenefitAddItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    detailSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    subDetailSequence: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    provider: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    productOrService: fhir_types.CodeableConcept
    modifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    programCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    servicedDate: FHIRDate | None = None
    servicedPeriod: fhir_types.Period | None = None
    locationCodeableConcept: fhir_types.CodeableConcept | None = None
    locationAddress: fhir_types.Address | None = None
    locationReference: fhir_types.Reference | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    unitPrice: fhir_types.Money | None = None
    factor: FHIRDecimal | None = None
    net: fhir_types.Money | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    subSite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    noteNumber: Annotated[list[FHIRPositiveInt], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
    detail: Annotated[list[ExplanationOfBenefitAddItemDetail], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitAddItem':
        _present = sum(1 for _f in ('servicedDate', 'servicedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('serviced[x] allows at most one value')
        _present = sum(1 for _f in ('locationCodeableConcept', 'locationAddress', 'locationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('location[x] allows at most one value')
        return self
class ExplanationOfBenefitTotal(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    amount: fhir_types.Money
class ExplanationOfBenefitPayment(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    adjustment: fhir_types.Money | None = None
    adjustmentReason: fhir_types.CodeableConcept | None = None
    date: FHIRDate | None = None
    amount: fhir_types.Money | None = None
    identifier: fhir_types.Identifier | None = None
class ExplanationOfBenefitProcessNote(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    number: FHIRPositiveInt | None = None
    type: Literal['display', 'print', 'printoper'] | None = None
    text: StrictStr | None = None
    language: fhir_types.CodeableConcept | None = None
class ExplanationOfBenefitBenefitBalanceFinancial(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    allowedUnsignedInt: FHIRUnsignedInt | None = None
    allowedString: StrictStr | None = None
    allowedMoney: fhir_types.Money | None = None
    usedUnsignedInt: FHIRUnsignedInt | None = None
    usedMoney: fhir_types.Money | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ExplanationOfBenefitBenefitBalanceFinancial':
        _present = sum(1 for _f in ('allowedUnsignedInt', 'allowedString', 'allowedMoney',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('allowed[x] allows at most one value')
        _present = sum(1 for _f in ('usedUnsignedInt', 'usedMoney',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('used[x] allows at most one value')
        return self
class ExplanationOfBenefitBenefitBalance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    excluded: StrictBool | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    network: fhir_types.CodeableConcept | None = None
    unit: fhir_types.CodeableConcept | None = None
    term: fhir_types.CodeableConcept | None = None
    financial: Annotated[list[ExplanationOfBenefitBenefitBalanceFinancial], Field(min_length=1)] | None = None
class ExplanationOfBenefit(DomainResourceR4):
    resourceType: Literal['ExplanationOfBenefit']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    type: fhir_types.CodeableConcept
    subType: fhir_types.CodeableConcept | None = None
    use: Literal['claim', 'preauthorization', 'predetermination']
    patient: fhir_types.Reference
    billablePeriod: fhir_types.Period | None = None
    created: FHIRDateTime
    enterer: fhir_types.Reference | None = None
    insurer: fhir_types.Reference
    provider: fhir_types.Reference
    priority: fhir_types.CodeableConcept | None = None
    fundsReserveRequested: fhir_types.CodeableConcept | None = None
    fundsReserve: fhir_types.CodeableConcept | None = None
    related: Annotated[list[ExplanationOfBenefitRelated], Field(min_length=1)] | None = None
    prescription: fhir_types.Reference | None = None
    originalPrescription: fhir_types.Reference | None = None
    payee: ExplanationOfBenefitPayee | None = None
    referral: fhir_types.Reference | None = None
    facility: fhir_types.Reference | None = None
    claim: fhir_types.Reference | None = None
    claimResponse: fhir_types.Reference | None = None
    outcome: Literal['complete', 'error', 'partial', 'queued']
    disposition: StrictStr | None = None
    preAuthRef: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    preAuthRefPeriod: Annotated[list[fhir_types.Period], Field(min_length=1)] | None = None
    careTeam: Annotated[list[ExplanationOfBenefitCareTeam], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[ExplanationOfBenefitSupportingInfo], Field(min_length=1)] | None = None
    diagnosis: Annotated[list[ExplanationOfBenefitDiagnosis], Field(min_length=1)] | None = None
    procedure: Annotated[list[ExplanationOfBenefitProcedure], Field(min_length=1)] | None = None
    precedence: FHIRPositiveInt | None = None
    insurance: Annotated[list[ExplanationOfBenefitInsurance], Field(min_length=1)]
    accident: ExplanationOfBenefitAccident | None = None
    item: Annotated[list[ExplanationOfBenefitItem], Field(min_length=1)] | None = None
    addItem: Annotated[list[ExplanationOfBenefitAddItem], Field(min_length=1)] | None = None
    adjudication: Annotated[list[ExplanationOfBenefitItemAdjudication], Field(min_length=1)] | None = None
    total: Annotated[list[ExplanationOfBenefitTotal], Field(min_length=1)] | None = None
    payment: ExplanationOfBenefitPayment | None = None
    formCode: fhir_types.CodeableConcept | None = None
    form: fhir_types.Attachment | None = None
    processNote: Annotated[list[ExplanationOfBenefitProcessNote], Field(min_length=1)] | None = None
    benefitPeriod: fhir_types.Period | None = None
    benefitBalance: Annotated[list[ExplanationOfBenefitBenefitBalance], Field(min_length=1)] | None = None

class FamilyMemberHistoryCondition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    outcome: fhir_types.CodeableConcept | None = None
    contributedToDeath: StrictBool | None = None
    onsetAge: fhir_types.Age | None = None
    onsetRange: fhir_types.Range | None = None
    onsetPeriod: fhir_types.Period | None = None
    onsetString: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'FamilyMemberHistoryCondition':
        _present = sum(1 for _f in ('onsetAge', 'onsetRange', 'onsetPeriod', 'onsetString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('onset[x] allows at most one value')
        return self
class FamilyMemberHistory(DomainResourceR4):
    resourceType: Literal['FamilyMemberHistory']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'health-unknown', 'partial']
    dataAbsentReason: fhir_types.CodeableConcept | None = None
    patient: fhir_types.Reference
    date: FHIRDateTime | None = None
    name: StrictStr | None = None
    relationship: fhir_types.CodeableConcept
    sex: fhir_types.CodeableConcept | None = None
    bornPeriod: fhir_types.Period | None = None
    bornDate: FHIRDate | None = None
    bornString: StrictStr | None = None
    ageAge: fhir_types.Age | None = None
    ageRange: fhir_types.Range | None = None
    ageString: StrictStr | None = None
    estimatedAge: StrictBool | None = None
    deceasedBoolean: StrictBool | None = None
    deceasedAge: fhir_types.Age | None = None
    deceasedRange: fhir_types.Range | None = None
    deceasedDate: FHIRDate | None = None
    deceasedString: StrictStr | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    condition: Annotated[list[FamilyMemberHistoryCondition], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'FamilyMemberHistory':
        _present = sum(1 for _f in ('bornPeriod', 'bornDate', 'bornString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('born[x] allows at most one value')
        _present = sum(1 for _f in ('ageAge', 'ageRange', 'ageString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('age[x] allows at most one value')
        _present = sum(1 for _f in ('deceasedBoolean', 'deceasedAge', 'deceasedRange', 'deceasedDate', 'deceasedString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('deceased[x] allows at most one value')
        return self

class Flag(DomainResourceR4):
    resourceType: Literal['Flag']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'inactive']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    subject: fhir_types.Reference
    period: fhir_types.Period | None = None
    encounter: fhir_types.Reference | None = None
    author: fhir_types.Reference | None = None

class GoalTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    measure: fhir_types.CodeableConcept | None = None
    detailQuantity: fhir_types.Quantity | None = None
    detailRange: fhir_types.Range | None = None
    detailCodeableConcept: fhir_types.CodeableConcept | None = None
    detailString: StrictStr | None = None
    detailBoolean: StrictBool | None = None
    detailInteger: FHIRInteger | None = None
    detailRatio: fhir_types.Ratio | None = None
    dueDate: FHIRDate | None = None
    dueDuration: fhir_types.Duration | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'GoalTarget':
        _present = sum(1 for _f in ('detailQuantity', 'detailRange', 'detailCodeableConcept', 'detailString', 'detailBoolean', 'detailInteger', 'detailRatio',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('detail[x] allows at most one value')
        _present = sum(1 for _f in ('dueDate', 'dueDuration',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('due[x] allows at most one value')
        return self
class Goal(DomainResourceR4):
    resourceType: Literal['Goal']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    lifecycleStatus: Literal['accepted', 'active', 'cancelled', 'completed', 'entered-in-error', 'on-hold', 'planned', 'proposed', 'rejected']
    achievementStatus: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    priority: fhir_types.CodeableConcept | None = None
    description: fhir_types.CodeableConcept
    subject: fhir_types.Reference
    startDate: FHIRDate | None = None
    startCodeableConcept: fhir_types.CodeableConcept | None = None
    target: Annotated[list[GoalTarget], Field(min_length=1)] | None = None
    statusDate: FHIRDate | None = None
    statusReason: StrictStr | None = None
    expressedBy: fhir_types.Reference | None = None
    addresses: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    outcomeCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    outcomeReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Goal':
        _present = sum(1 for _f in ('startDate', 'startCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('start[x] allows at most one value')
        return self

class GraphDefinitionLinkTargetCompartment(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    use: Literal['condition', 'requirement']
    code: Literal['Device', 'Encounter', 'Patient', 'Practitioner', 'RelatedPerson']
    rule: Literal['custom', 'different', 'identical', 'matching']
    expression: StrictStr | None = None
    description: StrictStr | None = None
class GraphDefinitionLinkTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: FHIRCode
    params: StrictStr | None = None
    profile: StrictStr | None = None
    compartment: Annotated[list[GraphDefinitionLinkTargetCompartment], Field(min_length=1)] | None = None
    link: Annotated[list[GraphDefinitionLink], Field(min_length=1)] | None = None
class GraphDefinitionLink(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    path: StrictStr | None = None
    sliceName: StrictStr | None = None
    min: FHIRInteger | None = None
    max: StrictStr | None = None
    description: StrictStr | None = None
    target: Annotated[list[GraphDefinitionLinkTarget], Field(min_length=1)] | None = None
class GraphDefinition(DomainResourceR4):
    resourceType: Literal['GraphDefinition']
    url: StrictStr | None = None
    version: StrictStr | None = None
    name: StrictStr
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    start: FHIRCode
    profile: StrictStr | None = None
    link: Annotated[list[GraphDefinitionLink], Field(min_length=1)] | None = None

class GroupCharacteristic(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueBoolean: StrictBool | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueReference: fhir_types.Reference | None = None
    exclude: StrictBool
    period: fhir_types.Period | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'GroupCharacteristic':
        _present = sum(1 for _f in ('valueCodeableConcept', 'valueBoolean', 'valueQuantity', 'valueRange', 'valueReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class GroupMember(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    entity: fhir_types.Reference
    period: fhir_types.Period | None = None
    inactive: StrictBool | None = None
class Group(DomainResourceR4):
    resourceType: Literal['Group']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    type: Literal['animal', 'device', 'medication', 'person', 'practitioner', 'substance']
    actual: StrictBool
    code: fhir_types.CodeableConcept | None = None
    name: StrictStr | None = None
    quantity: FHIRUnsignedInt | None = None
    managingEntity: fhir_types.Reference | None = None
    characteristic: Annotated[list[GroupCharacteristic], Field(min_length=1)] | None = None
    member: Annotated[list[GroupMember], Field(min_length=1)] | None = None

class GuidanceResponse(DomainResourceR4):
    resourceType: Literal['GuidanceResponse']
    requestIdentifier: fhir_types.Identifier | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    moduleUri: StrictStr | None = None
    moduleCanonical: StrictStr | None = None
    moduleCodeableConcept: fhir_types.CodeableConcept | None = None
    status: Literal['data-requested', 'data-required', 'entered-in-error', 'failure', 'in-progress', 'success']
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    performer: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    evaluationMessage: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    outputParameters: fhir_types.Reference | None = None
    result: fhir_types.Reference | None = None
    dataRequirement: Annotated[list[fhir_types.DataRequirement], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'GuidanceResponse':
        _present = sum(1 for _f in ('moduleUri', 'moduleCanonical', 'moduleCodeableConcept',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('module[x] requires exactly one value')
        return self

class HealthcareServiceEligibility(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    comment: StrictStr | None = None
class HealthcareServiceAvailableTime(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    daysOfWeek: Annotated[list[Literal['fri', 'mon', 'sat', 'sun', 'thu', 'tue', 'wed']], Field(min_length=1)] | None = None
    allDay: StrictBool | None = None
    availableStartTime: FHIRTime | None = None
    availableEndTime: FHIRTime | None = None
class HealthcareServiceNotAvailable(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr
    during: fhir_types.Period | None = None
class HealthcareService(DomainResourceR4):
    resourceType: Literal['HealthcareService']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    providedBy: fhir_types.Reference | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    location: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    comment: StrictStr | None = None
    extraDetails: StrictStr | None = None
    photo: fhir_types.Attachment | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    coverageArea: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    serviceProvisionCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    eligibility: Annotated[list[HealthcareServiceEligibility], Field(min_length=1)] | None = None
    program: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    characteristic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    communication: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    referralMethod: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    appointmentRequired: StrictBool | None = None
    availableTime: Annotated[list[HealthcareServiceAvailableTime], Field(min_length=1)] | None = None
    notAvailable: Annotated[list[HealthcareServiceNotAvailable], Field(min_length=1)] | None = None
    availabilityExceptions: StrictStr | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class ImagingStudySeriesPerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class ImagingStudySeriesInstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    uid: FHIRId
    sopClass: fhir_types.Coding
    number: FHIRUnsignedInt | None = None
    title: StrictStr | None = None
class ImagingStudySeries(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    uid: FHIRId
    number: FHIRUnsignedInt | None = None
    modality: fhir_types.Coding
    description: StrictStr | None = None
    numberOfInstances: FHIRUnsignedInt | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: fhir_types.Coding | None = None
    laterality: fhir_types.Coding | None = None
    specimen: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    started: FHIRDateTime | None = None
    performer: Annotated[list[ImagingStudySeriesPerformer], Field(min_length=1)] | None = None
    instance: Annotated[list[ImagingStudySeriesInstance], Field(min_length=1)] | None = None
class ImagingStudy(DomainResourceR4):
    resourceType: Literal['ImagingStudy']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['available', 'cancelled', 'entered-in-error', 'registered', 'unknown']
    modality: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    started: FHIRDateTime | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    referrer: fhir_types.Reference | None = None
    interpreter: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    numberOfSeries: FHIRUnsignedInt | None = None
    numberOfInstances: FHIRUnsignedInt | None = None
    procedureReference: fhir_types.Reference | None = None
    procedureCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    series: Annotated[list[ImagingStudySeries], Field(min_length=1)] | None = None

class ImmunizationPerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class ImmunizationEducation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    documentType: StrictStr | None = None
    reference: StrictStr | None = None
    publicationDate: FHIRDateTime | None = None
    presentationDate: FHIRDateTime | None = None
class ImmunizationReaction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    date: FHIRDateTime | None = None
    detail: fhir_types.Reference | None = None
    reported: StrictBool | None = None
class ImmunizationProtocolApplied(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    series: StrictStr | None = None
    authority: fhir_types.Reference | None = None
    targetDisease: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    doseNumberPositiveInt: FHIRPositiveInt | None = None
    doseNumberString: StrictStr | None = None
    seriesDosesPositiveInt: FHIRPositiveInt | None = None
    seriesDosesString: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImmunizationProtocolApplied':
        _present = sum(1 for _f in ('doseNumberPositiveInt', 'doseNumberString',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('doseNumber[x] requires exactly one value')
        _present = sum(1 for _f in ('seriesDosesPositiveInt', 'seriesDosesString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('seriesDoses[x] allows at most one value')
        return self
class Immunization(DomainResourceR4):
    resourceType: Literal['Immunization']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'not-done']
    statusReason: fhir_types.CodeableConcept | None = None
    vaccineCode: fhir_types.CodeableConcept
    patient: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrenceString: StrictStr | None = None
    recorded: FHIRDateTime | None = None
    primarySource: StrictBool | None = None
    reportOrigin: fhir_types.CodeableConcept | None = None
    location: fhir_types.Reference | None = None
    manufacturer: fhir_types.Reference | None = None
    lotNumber: StrictStr | None = None
    expirationDate: FHIRDate | None = None
    site: fhir_types.CodeableConcept | None = None
    route: fhir_types.CodeableConcept | None = None
    doseQuantity: fhir_types.SimpleQuantity | None = None
    performer: Annotated[list[ImmunizationPerformer], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    isSubpotent: StrictBool | None = None
    subpotentReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    education: Annotated[list[ImmunizationEducation], Field(min_length=1)] | None = None
    programEligibility: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    fundingSource: fhir_types.CodeableConcept | None = None
    reaction: Annotated[list[ImmunizationReaction], Field(min_length=1)] | None = None
    protocolApplied: Annotated[list[ImmunizationProtocolApplied], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Immunization':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrenceString',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('occurrence[x] requires exactly one value')
        return self

class ImmunizationEvaluation(DomainResourceR4):
    resourceType: Literal['ImmunizationEvaluation']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error']
    patient: fhir_types.Reference
    date: FHIRDateTime | None = None
    authority: fhir_types.Reference | None = None
    targetDisease: fhir_types.CodeableConcept
    immunizationEvent: fhir_types.Reference
    doseStatus: fhir_types.CodeableConcept
    doseStatusReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    series: StrictStr | None = None
    doseNumberPositiveInt: FHIRPositiveInt | None = None
    doseNumberString: StrictStr | None = None
    seriesDosesPositiveInt: FHIRPositiveInt | None = None
    seriesDosesString: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImmunizationEvaluation':
        _present = sum(1 for _f in ('doseNumberPositiveInt', 'doseNumberString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('doseNumber[x] allows at most one value')
        _present = sum(1 for _f in ('seriesDosesPositiveInt', 'seriesDosesString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('seriesDoses[x] allows at most one value')
        return self

class ImmunizationRecommendationRecommendationDateCriterion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    value: FHIRDateTime
class ImmunizationRecommendationRecommendation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    vaccineCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    targetDisease: fhir_types.CodeableConcept | None = None
    contraindicatedVaccineCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    forecastStatus: fhir_types.CodeableConcept
    forecastReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    dateCriterion: Annotated[list[ImmunizationRecommendationRecommendationDateCriterion], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    series: StrictStr | None = None
    doseNumberPositiveInt: FHIRPositiveInt | None = None
    doseNumberString: StrictStr | None = None
    seriesDosesPositiveInt: FHIRPositiveInt | None = None
    seriesDosesString: StrictStr | None = None
    supportingImmunization: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    supportingPatientInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImmunizationRecommendationRecommendation':
        _present = sum(1 for _f in ('doseNumberPositiveInt', 'doseNumberString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('doseNumber[x] allows at most one value')
        _present = sum(1 for _f in ('seriesDosesPositiveInt', 'seriesDosesString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('seriesDoses[x] allows at most one value')
        return self
class ImmunizationRecommendation(DomainResourceR4):
    resourceType: Literal['ImmunizationRecommendation']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    patient: fhir_types.Reference
    date: FHIRDateTime
    authority: fhir_types.Reference | None = None
    recommendation: Annotated[list[ImmunizationRecommendationRecommendation], Field(min_length=1)]

class ImplementationGuideDependsOn(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    uri: StrictStr
    packageId: FHIRId | None = None
    version: StrictStr | None = None
class ImplementationGuideGlobal(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: FHIRCode
    profile: StrictStr
class ImplementationGuideDefinitionGrouping(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    description: StrictStr | None = None
class ImplementationGuideDefinitionResource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    reference: fhir_types.Reference
    fhirVersion: Annotated[list[Literal['0.0.80', '0.0.81', '0.0.82', '0.01', '0.05', '0.06', '0.11', '0.4.0', '0.5.0', '1.0.0', '1.0.1', '1.0.2', '1.1.0', '1.4.0', '1.6.0', '1.8.0', '3.0.0', '3.0.1', '3.3.0', '3.5.0', '4.0.0', '4.0.1']], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    exampleBoolean: StrictBool | None = None
    exampleCanonical: StrictStr | None = None
    groupingId: FHIRId | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImplementationGuideDefinitionResource':
        _present = sum(1 for _f in ('exampleBoolean', 'exampleCanonical',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('example[x] allows at most one value')
        return self
class ImplementationGuideDefinitionPage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    nameUrl: StrictStr | None = None
    nameReference: fhir_types.Reference | None = None
    title: StrictStr
    generation: Literal['generated', 'html', 'markdown', 'xml']
    page: Annotated[list[ImplementationGuideDefinitionPage], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImplementationGuideDefinitionPage':
        _present = sum(1 for _f in ('nameUrl', 'nameReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('name[x] requires exactly one value')
        return self
class ImplementationGuideDefinitionParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Literal['apply', 'expansion-parameter', 'generate-json', 'generate-turtle', 'generate-xml', 'html-template', 'path-pages', 'path-resource', 'path-tx-cache', 'rule-broken-links']
    value: StrictStr
class ImplementationGuideDefinitionTemplate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    source: StrictStr
    scope: StrictStr | None = None
class ImplementationGuideDefinition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    grouping: Annotated[list[ImplementationGuideDefinitionGrouping], Field(min_length=1)] | None = None
    resource: Annotated[list[ImplementationGuideDefinitionResource], Field(min_length=1)]
    page: ImplementationGuideDefinitionPage | None = None
    parameter: Annotated[list[ImplementationGuideDefinitionParameter], Field(min_length=1)] | None = None
    template: Annotated[list[ImplementationGuideDefinitionTemplate], Field(min_length=1)] | None = None
class ImplementationGuideManifestResource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    reference: fhir_types.Reference
    exampleBoolean: StrictBool | None = None
    exampleCanonical: StrictStr | None = None
    relativePath: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ImplementationGuideManifestResource':
        _present = sum(1 for _f in ('exampleBoolean', 'exampleCanonical',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('example[x] allows at most one value')
        return self
class ImplementationGuideManifestPage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    title: StrictStr | None = None
    anchor: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class ImplementationGuideManifest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    rendering: StrictStr | None = None
    resource: Annotated[list[ImplementationGuideManifestResource], Field(min_length=1)]
    page: Annotated[list[ImplementationGuideManifestPage], Field(min_length=1)] | None = None
    image: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    other: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class ImplementationGuide(DomainResourceR4):
    resourceType: Literal['ImplementationGuide']
    url: StrictStr
    version: StrictStr | None = None
    name: StrictStr
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    packageId: FHIRId
    license: FHIRCode | None = None
    fhirVersion: Annotated[list[Literal['0.0.80', '0.0.81', '0.0.82', '0.01', '0.05', '0.06', '0.11', '0.4.0', '0.5.0', '1.0.0', '1.0.1', '1.0.2', '1.1.0', '1.4.0', '1.6.0', '1.8.0', '3.0.0', '3.0.1', '3.3.0', '3.5.0', '4.0.0', '4.0.1']], Field(min_length=1)]
    dependsOn: Annotated[list[ImplementationGuideDependsOn], Field(min_length=1)] | None = None
    global_: Annotated[list[ImplementationGuideGlobal], Field(min_length=1)] | None = Field(default=None, alias='global')
    definition: ImplementationGuideDefinition | None = None
    manifest: ImplementationGuideManifest | None = None

class InsurancePlanContact(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    purpose: fhir_types.CodeableConcept | None = None
    name: fhir_types.HumanName | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: fhir_types.Address | None = None
class InsurancePlanCoverageBenefitLimit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    value: fhir_types.Quantity | None = None
    code: fhir_types.CodeableConcept | None = None
class InsurancePlanCoverageBenefit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    requirement: StrictStr | None = None
    limit: Annotated[list[InsurancePlanCoverageBenefitLimit], Field(min_length=1)] | None = None
class InsurancePlanCoverage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    network: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    benefit: Annotated[list[InsurancePlanCoverageBenefit], Field(min_length=1)]
class InsurancePlanPlanGeneralCost(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    groupSize: FHIRPositiveInt | None = None
    cost: fhir_types.Money | None = None
    comment: StrictStr | None = None
class InsurancePlanPlanSpecificCostBenefitCost(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    applicability: fhir_types.CodeableConcept | None = None
    qualifiers: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    value: fhir_types.Quantity | None = None
class InsurancePlanPlanSpecificCostBenefit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    cost: Annotated[list[InsurancePlanPlanSpecificCostBenefitCost], Field(min_length=1)] | None = None
class InsurancePlanPlanSpecificCost(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept
    benefit: Annotated[list[InsurancePlanPlanSpecificCostBenefit], Field(min_length=1)] | None = None
class InsurancePlanPlan(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    coverageArea: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    network: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    generalCost: Annotated[list[InsurancePlanPlanGeneralCost], Field(min_length=1)] | None = None
    specificCost: Annotated[list[InsurancePlanPlanSpecificCost], Field(min_length=1)] | None = None
class InsurancePlan(DomainResourceR4):
    resourceType: Literal['InsurancePlan']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'retired', 'unknown'] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    alias: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    ownedBy: fhir_types.Reference | None = None
    administeredBy: fhir_types.Reference | None = None
    coverageArea: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    contact: Annotated[list[InsurancePlanContact], Field(min_length=1)] | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    network: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    coverage: Annotated[list[InsurancePlanCoverage], Field(min_length=1)] | None = None
    plan: Annotated[list[InsurancePlanPlan], Field(min_length=1)] | None = None

class InvoiceParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    role: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class InvoiceLineItemPriceComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['base', 'deduction', 'discount', 'informational', 'surcharge', 'tax']
    code: fhir_types.CodeableConcept | None = None
    factor: FHIRDecimal | None = None
    amount: fhir_types.Money | None = None
class InvoiceLineItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    sequence: FHIRPositiveInt | None = None
    chargeItemReference: fhir_types.Reference | None = None
    chargeItemCodeableConcept: fhir_types.CodeableConcept | None = None
    priceComponent: Annotated[list[InvoiceLineItemPriceComponent], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'InvoiceLineItem':
        _present = sum(1 for _f in ('chargeItemReference', 'chargeItemCodeableConcept',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('chargeItem[x] requires exactly one value')
        return self
class Invoice(DomainResourceR4):
    resourceType: Literal['Invoice']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['balanced', 'cancelled', 'draft', 'entered-in-error', 'issued']
    cancelledReason: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    recipient: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    participant: Annotated[list[InvoiceParticipant], Field(min_length=1)] | None = None
    issuer: fhir_types.Reference | None = None
    account: fhir_types.Reference | None = None
    lineItem: Annotated[list[InvoiceLineItem], Field(min_length=1)] | None = None
    totalPriceComponent: Annotated[list[InvoiceLineItemPriceComponent], Field(min_length=1)] | None = None
    totalNet: fhir_types.Money | None = None
    totalGross: fhir_types.Money | None = None
    paymentTerms: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class Library(DomainResourceR4):
    resourceType: Literal['Library']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    type: fhir_types.CodeableConcept
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    parameter: Annotated[list[fhir_types.ParameterDefinition], Field(min_length=1)] | None = None
    dataRequirement: Annotated[list[fhir_types.DataRequirement], Field(min_length=1)] | None = None
    content: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Library':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class LinkageItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['alternate', 'historical', 'source']
    resource: fhir_types.Reference
class Linkage(DomainResourceR4):
    resourceType: Literal['Linkage']
    active: StrictBool | None = None
    author: fhir_types.Reference | None = None
    item: Annotated[list[LinkageItem], Field(min_length=1)]

class ListEntry(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    flag: fhir_types.CodeableConcept | None = None
    deleted: StrictBool | None = None
    date: FHIRDateTime | None = None
    item: fhir_types.Reference
class List(DomainResourceR4):
    resourceType: Literal['List']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['current', 'entered-in-error', 'retired']
    mode: Literal['changes', 'snapshot', 'working']
    title: StrictStr | None = None
    code: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    source: fhir_types.Reference | None = None
    orderedBy: fhir_types.CodeableConcept | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    entry: Annotated[list[ListEntry], Field(min_length=1)] | None = None
    emptyReason: fhir_types.CodeableConcept | None = None

class LocationPosition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    longitude: FHIRDecimal
    latitude: FHIRDecimal
    altitude: FHIRDecimal | None = None
class LocationHoursOfOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    daysOfWeek: Annotated[list[Literal['fri', 'mon', 'sat', 'sun', 'thu', 'tue', 'wed']], Field(min_length=1)] | None = None
    allDay: StrictBool | None = None
    openingTime: FHIRTime | None = None
    closingTime: FHIRTime | None = None
class Location(DomainResourceR4):
    resourceType: Literal['Location']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'inactive', 'suspended'] | None = None
    operationalStatus: fhir_types.Coding | None = None
    name: StrictStr | None = None
    alias: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    mode: Literal['instance', 'kind'] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: fhir_types.Address | None = None
    physicalType: fhir_types.CodeableConcept | None = None
    position: LocationPosition | None = None
    managingOrganization: fhir_types.Reference | None = None
    partOf: fhir_types.Reference | None = None
    hoursOfOperation: Annotated[list[LocationHoursOfOperation], Field(min_length=1)] | None = None
    availabilityExceptions: StrictStr | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class MeasureGroupPopulation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    criteria: fhir_types.Expression
class MeasureGroupStratifierComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    criteria: fhir_types.Expression
class MeasureGroupStratifier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    criteria: fhir_types.Expression | None = None
    component: Annotated[list[MeasureGroupStratifierComponent], Field(min_length=1)] | None = None
class MeasureGroup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    population: Annotated[list[MeasureGroupPopulation], Field(min_length=1)] | None = None
    stratifier: Annotated[list[MeasureGroupStratifier], Field(min_length=1)] | None = None
class MeasureSupplementalData(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    usage: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    criteria: fhir_types.Expression
class Measure(DomainResourceR4):
    resourceType: Literal['Measure']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    library: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    disclaimer: StrictStr | None = None
    scoring: fhir_types.CodeableConcept | None = None
    compositeScoring: fhir_types.CodeableConcept | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    riskAdjustment: StrictStr | None = None
    rateAggregation: StrictStr | None = None
    rationale: StrictStr | None = None
    clinicalRecommendationStatement: StrictStr | None = None
    improvementNotation: fhir_types.CodeableConcept | None = None
    definition: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    guidance: StrictStr | None = None
    group: Annotated[list[MeasureGroup], Field(min_length=1)] | None = None
    supplementalData: Annotated[list[MeasureSupplementalData], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Measure':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class MeasureReportGroupPopulation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    count: FHIRInteger | None = None
    subjectResults: fhir_types.Reference | None = None
class MeasureReportGroupStratifierStratumComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    value: fhir_types.CodeableConcept
class MeasureReportGroupStratifierStratumPopulation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    count: FHIRInteger | None = None
    subjectResults: fhir_types.Reference | None = None
class MeasureReportGroupStratifierStratum(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    value: fhir_types.CodeableConcept | None = None
    component: Annotated[list[MeasureReportGroupStratifierStratumComponent], Field(min_length=1)] | None = None
    population: Annotated[list[MeasureReportGroupStratifierStratumPopulation], Field(min_length=1)] | None = None
    measureScore: fhir_types.Quantity | None = None
class MeasureReportGroupStratifier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    stratum: Annotated[list[MeasureReportGroupStratifierStratum], Field(min_length=1)] | None = None
class MeasureReportGroup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    population: Annotated[list[MeasureReportGroupPopulation], Field(min_length=1)] | None = None
    measureScore: fhir_types.Quantity | None = None
    stratifier: Annotated[list[MeasureReportGroupStratifier], Field(min_length=1)] | None = None
class MeasureReport(DomainResourceR4):
    resourceType: Literal['MeasureReport']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['complete', 'error', 'pending']
    type: Literal['data-collection', 'individual', 'subject-list', 'summary']
    measure: StrictStr
    subject: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    reporter: fhir_types.Reference | None = None
    period: fhir_types.Period
    improvementNotation: fhir_types.CodeableConcept | None = None
    group: Annotated[list[MeasureReportGroup], Field(min_length=1)] | None = None
    evaluatedResource: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class Media(DomainResourceR4):
    resourceType: Literal['Media']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress', 'not-done', 'on-hold', 'preparation', 'stopped', 'unknown']
    type: fhir_types.CodeableConcept | None = None
    modality: fhir_types.CodeableConcept | None = None
    view: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    createdDateTime: FHIRDateTime | None = None
    createdPeriod: fhir_types.Period | None = None
    issued: FHIRInstant | None = None
    operator: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    deviceName: StrictStr | None = None
    device: fhir_types.Reference | None = None
    height: FHIRPositiveInt | None = None
    width: FHIRPositiveInt | None = None
    frames: FHIRPositiveInt | None = None
    duration: FHIRDecimal | None = None
    content: fhir_types.Attachment
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Media':
        _present = sum(1 for _f in ('createdDateTime', 'createdPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('created[x] allows at most one value')
        return self

class MedicationIngredient(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None
    itemReference: fhir_types.Reference | None = None
    isActive: StrictBool | None = None
    strength: fhir_types.Ratio | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationIngredient':
        _present = sum(1 for _f in ('itemCodeableConcept', 'itemReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('item[x] requires exactly one value')
        return self
class MedicationBatch(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    lotNumber: StrictStr | None = None
    expirationDate: FHIRDateTime | None = None
class Medication(DomainResourceR4):
    resourceType: Literal['Medication']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    status: Literal['active', 'entered-in-error', 'inactive'] | None = None
    manufacturer: fhir_types.Reference | None = None
    form: fhir_types.CodeableConcept | None = None
    amount: fhir_types.Ratio | None = None
    ingredient: Annotated[list[MedicationIngredient], Field(min_length=1)] | None = None
    batch: MedicationBatch | None = None

class MedicationAdministrationPerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class MedicationAdministrationDosage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    text: StrictStr | None = None
    site: fhir_types.CodeableConcept | None = None
    route: fhir_types.CodeableConcept | None = None
    method: fhir_types.CodeableConcept | None = None
    dose: fhir_types.SimpleQuantity | None = None
    rateRatio: fhir_types.Ratio | None = None
    rateQuantity: fhir_types.SimpleQuantity | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationAdministrationDosage':
        _present = sum(1 for _f in ('rateRatio', 'rateQuantity',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('rate[x] allows at most one value')
        return self
class MedicationAdministration(DomainResourceR4):
    resourceType: Literal['MedicationAdministration']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiates: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress', 'not-done', 'on-hold', 'stopped', 'unknown']
    statusReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None
    subject: fhir_types.Reference
    context: fhir_types.Reference | None = None
    supportingInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    effectiveDateTime: FHIRDateTime | None = None
    effectivePeriod: fhir_types.Period | None = None
    performer: Annotated[list[MedicationAdministrationPerformer], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    request: fhir_types.Reference | None = None
    device: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    dosage: MedicationAdministrationDosage | None = None
    eventHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationAdministration':
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        _present = sum(1 for _f in ('effectiveDateTime', 'effectivePeriod',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('effective[x] requires exactly one value')
        return self

class MedicationDispensePerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
class MedicationDispenseSubstitution(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    wasSubstituted: StrictBool
    type: fhir_types.CodeableConcept | None = None
    reason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    responsibleParty: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class MedicationDispense(DomainResourceR4):
    resourceType: Literal['MedicationDispense']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['cancelled', 'completed', 'declined', 'entered-in-error', 'in-progress', 'on-hold', 'preparation', 'stopped', 'unknown']
    statusReasonCodeableConcept: fhir_types.CodeableConcept | None = None
    statusReasonReference: fhir_types.Reference | None = None
    category: fhir_types.CodeableConcept | None = None
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None
    subject: fhir_types.Reference | None = None
    context: fhir_types.Reference | None = None
    supportingInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    performer: Annotated[list[MedicationDispensePerformer], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    authorizingPrescription: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    daysSupply: fhir_types.SimpleQuantity | None = None
    whenPrepared: FHIRDateTime | None = None
    whenHandedOver: FHIRDateTime | None = None
    destination: fhir_types.Reference | None = None
    receiver: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    dosageInstruction: Annotated[list[fhir_types.Dosage], Field(min_length=1)] | None = None
    substitution: MedicationDispenseSubstitution | None = None
    detectedIssue: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    eventHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationDispense':
        _present = sum(1 for _f in ('statusReasonCodeableConcept', 'statusReasonReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('statusReason[x] allows at most one value')
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        return self

class MedicationKnowledgeRelatedMedicationKnowledge(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    reference: Annotated[list[fhir_types.Reference], Field(min_length=1)]
class MedicationKnowledgeMonograph(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    source: fhir_types.Reference | None = None
class MedicationKnowledgeIngredient(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None
    itemReference: fhir_types.Reference | None = None
    isActive: StrictBool | None = None
    strength: fhir_types.Ratio | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationKnowledgeIngredient':
        _present = sum(1 for _f in ('itemCodeableConcept', 'itemReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('item[x] requires exactly one value')
        return self
class MedicationKnowledgeCost(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    source: StrictStr | None = None
    cost: fhir_types.Money
class MedicationKnowledgeMonitoringProgram(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    name: StrictStr | None = None
class MedicationKnowledgeAdministrationGuidelinesDosage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    dosage: Annotated[list[fhir_types.Dosage], Field(min_length=1)]
class MedicationKnowledgeAdministrationGuidelinesPatientCharacteristics(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    characteristicCodeableConcept: fhir_types.CodeableConcept | None = None
    characteristicQuantity: fhir_types.SimpleQuantity | None = None
    value: Annotated[list[StrictStr], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationKnowledgeAdministrationGuidelinesPatientCharacteristics':
        _present = sum(1 for _f in ('characteristicCodeableConcept', 'characteristicQuantity',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('characteristic[x] requires exactly one value')
        return self
class MedicationKnowledgeAdministrationGuidelines(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    dosage: Annotated[list[MedicationKnowledgeAdministrationGuidelinesDosage], Field(min_length=1)] | None = None
    indicationCodeableConcept: fhir_types.CodeableConcept | None = None
    indicationReference: fhir_types.Reference | None = None
    patientCharacteristics: Annotated[list[MedicationKnowledgeAdministrationGuidelinesPatientCharacteristics], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationKnowledgeAdministrationGuidelines':
        _present = sum(1 for _f in ('indicationCodeableConcept', 'indicationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('indication[x] allows at most one value')
        return self
class MedicationKnowledgeMedicineClassification(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    classification: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class MedicationKnowledgePackaging(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    quantity: fhir_types.SimpleQuantity | None = None
class MedicationKnowledgeDrugCharacteristic(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueString: StrictStr | None = None
    valueQuantity: fhir_types.SimpleQuantity | None = None
    valueBase64Binary: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationKnowledgeDrugCharacteristic':
        _present = sum(1 for _f in ('valueCodeableConcept', 'valueString', 'valueQuantity', 'valueBase64Binary',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class MedicationKnowledgeRegulatorySubstitution(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    allowed: StrictBool
class MedicationKnowledgeRegulatorySchedule(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    schedule: fhir_types.CodeableConcept
class MedicationKnowledgeRegulatoryMaxDispense(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity
    period: fhir_types.Duration | None = None
class MedicationKnowledgeRegulatory(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    regulatoryAuthority: fhir_types.Reference
    substitution: Annotated[list[MedicationKnowledgeRegulatorySubstitution], Field(min_length=1)] | None = None
    schedule: Annotated[list[MedicationKnowledgeRegulatorySchedule], Field(min_length=1)] | None = None
    maxDispense: MedicationKnowledgeRegulatoryMaxDispense | None = None
class MedicationKnowledgeKinetics(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    areaUnderCurve: Annotated[list[fhir_types.SimpleQuantity], Field(min_length=1)] | None = None
    lethalDose50: Annotated[list[fhir_types.SimpleQuantity], Field(min_length=1)] | None = None
    halfLifePeriod: fhir_types.Duration | None = None
class MedicationKnowledge(DomainResourceR4):
    resourceType: Literal['MedicationKnowledge']
    code: fhir_types.CodeableConcept | None = None
    status: Literal['active', 'entered-in-error', 'inactive'] | None = None
    manufacturer: fhir_types.Reference | None = None
    doseForm: fhir_types.CodeableConcept | None = None
    amount: fhir_types.SimpleQuantity | None = None
    synonym: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    relatedMedicationKnowledge: Annotated[list[MedicationKnowledgeRelatedMedicationKnowledge], Field(min_length=1)] | None = None
    associatedMedication: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    productType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    monograph: Annotated[list[MedicationKnowledgeMonograph], Field(min_length=1)] | None = None
    ingredient: Annotated[list[MedicationKnowledgeIngredient], Field(min_length=1)] | None = None
    preparationInstruction: StrictStr | None = None
    intendedRoute: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    cost: Annotated[list[MedicationKnowledgeCost], Field(min_length=1)] | None = None
    monitoringProgram: Annotated[list[MedicationKnowledgeMonitoringProgram], Field(min_length=1)] | None = None
    administrationGuidelines: Annotated[list[MedicationKnowledgeAdministrationGuidelines], Field(min_length=1)] | None = None
    medicineClassification: Annotated[list[MedicationKnowledgeMedicineClassification], Field(min_length=1)] | None = None
    packaging: MedicationKnowledgePackaging | None = None
    drugCharacteristic: Annotated[list[MedicationKnowledgeDrugCharacteristic], Field(min_length=1)] | None = None
    contraindication: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    regulatory: Annotated[list[MedicationKnowledgeRegulatory], Field(min_length=1)] | None = None
    kinetics: Annotated[list[MedicationKnowledgeKinetics], Field(min_length=1)] | None = None

class MedicationRequestDispenseRequestInitialFill(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    duration: fhir_types.Duration | None = None
class MedicationRequestDispenseRequest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    initialFill: MedicationRequestDispenseRequestInitialFill | None = None
    dispenseInterval: fhir_types.Duration | None = None
    validityPeriod: fhir_types.Period | None = None
    numberOfRepeatsAllowed: FHIRUnsignedInt | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    expectedSupplyDuration: fhir_types.Duration | None = None
    performer: fhir_types.Reference | None = None
class MedicationRequestSubstitution(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    allowedBoolean: StrictBool | None = None
    allowedCodeableConcept: fhir_types.CodeableConcept | None = None
    reason: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationRequestSubstitution':
        _present = sum(1 for _f in ('allowedBoolean', 'allowedCodeableConcept',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('allowed[x] requires exactly one value')
        return self
class MedicationRequest(DomainResourceR4):
    resourceType: Literal['MedicationRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'completed', 'draft', 'entered-in-error', 'on-hold', 'stopped', 'unknown']
    statusReason: fhir_types.CodeableConcept | None = None
    intent: Literal['filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    doNotPerform: StrictBool | None = None
    reportedBoolean: StrictBool | None = None
    reportedReference: fhir_types.Reference | None = None
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    supportingInformation: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    authoredOn: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    performer: fhir_types.Reference | None = None
    performerType: fhir_types.CodeableConcept | None = None
    recorder: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    groupIdentifier: fhir_types.Identifier | None = None
    courseOfTherapyType: fhir_types.CodeableConcept | None = None
    insurance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    dosageInstruction: Annotated[list[fhir_types.Dosage], Field(min_length=1)] | None = None
    dispenseRequest: MedicationRequestDispenseRequest | None = None
    substitution: MedicationRequestSubstitution | None = None
    priorPrescription: fhir_types.Reference | None = None
    detectedIssue: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    eventHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationRequest':
        _present = sum(1 for _f in ('reportedBoolean', 'reportedReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('reported[x] allows at most one value')
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        return self

class MedicationStatement(DomainResourceR4):
    resourceType: Literal['MedicationStatement']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['active', 'completed', 'entered-in-error', 'intended', 'not-taken', 'on-hold', 'stopped', 'unknown']
    statusReason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None
    subject: fhir_types.Reference
    context: fhir_types.Reference | None = None
    effectiveDateTime: FHIRDateTime | None = None
    effectivePeriod: fhir_types.Period | None = None
    dateAsserted: FHIRDateTime | None = None
    informationSource: fhir_types.Reference | None = None
    derivedFrom: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    dosage: Annotated[list[fhir_types.Dosage], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicationStatement':
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        _present = sum(1 for _f in ('effectiveDateTime', 'effectivePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('effective[x] allows at most one value')
        return self

class MedicinalProductNameNamePart(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    part: StrictStr
    type: fhir_types.Coding
class MedicinalProductNameCountryLanguage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    country: fhir_types.CodeableConcept
    jurisdiction: fhir_types.CodeableConcept | None = None
    language: fhir_types.CodeableConcept
class MedicinalProductName(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    productName: StrictStr
    namePart: Annotated[list[MedicinalProductNameNamePart], Field(min_length=1)] | None = None
    countryLanguage: Annotated[list[MedicinalProductNameCountryLanguage], Field(min_length=1)] | None = None
class MedicinalProductManufacturingBusinessOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operationType: fhir_types.CodeableConcept | None = None
    authorisationReferenceNumber: fhir_types.Identifier | None = None
    effectiveDate: FHIRDateTime | None = None
    confidentialityIndicator: fhir_types.CodeableConcept | None = None
    manufacturer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    regulator: fhir_types.Reference | None = None
class MedicinalProductSpecialDesignation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    intendedUse: fhir_types.CodeableConcept | None = None
    indicationCodeableConcept: fhir_types.CodeableConcept | None = None
    indicationReference: fhir_types.Reference | None = None
    status: fhir_types.CodeableConcept | None = None
    date: FHIRDateTime | None = None
    species: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicinalProductSpecialDesignation':
        _present = sum(1 for _f in ('indicationCodeableConcept', 'indicationReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('indication[x] allows at most one value')
        return self
class MedicinalProduct(DomainResourceR4):
    resourceType: Literal['MedicinalProduct']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    domain: fhir_types.Coding | None = None
    combinedPharmaceuticalDoseForm: fhir_types.CodeableConcept | None = None
    legalStatusOfSupply: fhir_types.CodeableConcept | None = None
    additionalMonitoringIndicator: fhir_types.CodeableConcept | None = None
    specialMeasures: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    paediatricUseIndicator: fhir_types.CodeableConcept | None = None
    productClassification: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    marketingStatus: Annotated[list[fhir_types.MarketingStatus], Field(min_length=1)] | None = None
    pharmaceuticalProduct: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    packagedMedicinalProduct: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    attachedDocument: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    masterFile: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    contact: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    clinicalTrial: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    name: Annotated[list[MedicinalProductName], Field(min_length=1)]
    crossReference: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    manufacturingBusinessOperation: Annotated[list[MedicinalProductManufacturingBusinessOperation], Field(min_length=1)] | None = None
    specialDesignation: Annotated[list[MedicinalProductSpecialDesignation], Field(min_length=1)] | None = None

class MedicinalProductAuthorizationJurisdictionalAuthorization(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    country: fhir_types.CodeableConcept | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    legalStatusOfSupply: fhir_types.CodeableConcept | None = None
    validityPeriod: fhir_types.Period | None = None
class MedicinalProductAuthorizationProcedure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    type: fhir_types.CodeableConcept
    datePeriod: fhir_types.Period | None = None
    dateDateTime: FHIRDateTime | None = None
    application: Annotated[list[MedicinalProductAuthorizationProcedure], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicinalProductAuthorizationProcedure':
        _present = sum(1 for _f in ('datePeriod', 'dateDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('date[x] allows at most one value')
        return self
class MedicinalProductAuthorization(DomainResourceR4):
    resourceType: Literal['MedicinalProductAuthorization']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    subject: fhir_types.Reference | None = None
    country: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    status: fhir_types.CodeableConcept | None = None
    statusDate: FHIRDateTime | None = None
    restoreDate: FHIRDateTime | None = None
    validityPeriod: fhir_types.Period | None = None
    dataExclusivityPeriod: fhir_types.Period | None = None
    dateOfFirstAuthorization: FHIRDateTime | None = None
    internationalBirthDate: FHIRDateTime | None = None
    legalBasis: fhir_types.CodeableConcept | None = None
    jurisdictionalAuthorization: Annotated[list[MedicinalProductAuthorizationJurisdictionalAuthorization], Field(min_length=1)] | None = None
    holder: fhir_types.Reference | None = None
    regulator: fhir_types.Reference | None = None
    procedure: MedicinalProductAuthorizationProcedure | None = None

class MedicinalProductContraindicationOtherTherapy(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    therapyRelationshipType: fhir_types.CodeableConcept
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicinalProductContraindicationOtherTherapy':
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        return self
class MedicinalProductContraindication(DomainResourceR4):
    resourceType: Literal['MedicinalProductContraindication']
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    disease: fhir_types.CodeableConcept | None = None
    diseaseStatus: fhir_types.CodeableConcept | None = None
    comorbidity: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    therapeuticIndication: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    otherTherapy: Annotated[list[MedicinalProductContraindicationOtherTherapy], Field(min_length=1)] | None = None
    population: Annotated[list[fhir_types.Population], Field(min_length=1)] | None = None

class MedicinalProductIndicationOtherTherapy(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    therapyRelationshipType: fhir_types.CodeableConcept
    medicationCodeableConcept: fhir_types.CodeableConcept | None = None
    medicationReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicinalProductIndicationOtherTherapy':
        _present = sum(1 for _f in ('medicationCodeableConcept', 'medicationReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('medication[x] requires exactly one value')
        return self
class MedicinalProductIndication(DomainResourceR4):
    resourceType: Literal['MedicinalProductIndication']
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    diseaseSymptomProcedure: fhir_types.CodeableConcept | None = None
    diseaseStatus: fhir_types.CodeableConcept | None = None
    comorbidity: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    intendedEffect: fhir_types.CodeableConcept | None = None
    duration: fhir_types.Quantity | None = None
    otherTherapy: Annotated[list[MedicinalProductIndicationOtherTherapy], Field(min_length=1)] | None = None
    undesirableEffect: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    population: Annotated[list[fhir_types.Population], Field(min_length=1)] | None = None

class MedicinalProductIngredientSpecifiedSubstanceStrengthReferenceStrength(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    substance: fhir_types.CodeableConcept | None = None
    strength: fhir_types.Ratio
    strengthLowLimit: fhir_types.Ratio | None = None
    measurementPoint: StrictStr | None = None
    country: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class MedicinalProductIngredientSpecifiedSubstanceStrength(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    presentation: fhir_types.Ratio
    presentationLowLimit: fhir_types.Ratio | None = None
    concentration: fhir_types.Ratio | None = None
    concentrationLowLimit: fhir_types.Ratio | None = None
    measurementPoint: StrictStr | None = None
    country: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    referenceStrength: Annotated[list[MedicinalProductIngredientSpecifiedSubstanceStrengthReferenceStrength], Field(min_length=1)] | None = None
class MedicinalProductIngredientSpecifiedSubstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    group: fhir_types.CodeableConcept
    confidentiality: fhir_types.CodeableConcept | None = None
    strength: Annotated[list[MedicinalProductIngredientSpecifiedSubstanceStrength], Field(min_length=1)] | None = None
class MedicinalProductIngredientSubstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    strength: Annotated[list[MedicinalProductIngredientSpecifiedSubstanceStrength], Field(min_length=1)] | None = None
class MedicinalProductIngredient(DomainResourceR4):
    resourceType: Literal['MedicinalProductIngredient']
    identifier: fhir_types.Identifier | None = None
    role: fhir_types.CodeableConcept
    allergenicIndicator: StrictBool | None = None
    manufacturer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    specifiedSubstance: Annotated[list[MedicinalProductIngredientSpecifiedSubstance], Field(min_length=1)] | None = None
    substance: MedicinalProductIngredientSubstance | None = None

class MedicinalProductInteractionInteractant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    itemReference: fhir_types.Reference | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MedicinalProductInteractionInteractant':
        _present = sum(1 for _f in ('itemReference', 'itemCodeableConcept',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('item[x] requires exactly one value')
        return self
class MedicinalProductInteraction(DomainResourceR4):
    resourceType: Literal['MedicinalProductInteraction']
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    interactant: Annotated[list[MedicinalProductInteractionInteractant], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    effect: fhir_types.CodeableConcept | None = None
    incidence: fhir_types.CodeableConcept | None = None
    management: fhir_types.CodeableConcept | None = None

class MedicinalProductManufactured(DomainResourceR4):
    resourceType: Literal['MedicinalProductManufactured']
    manufacturedDoseForm: fhir_types.CodeableConcept
    unitOfPresentation: fhir_types.CodeableConcept | None = None
    quantity: fhir_types.Quantity
    manufacturer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    ingredient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    physicalCharacteristics: fhir_types.ProdCharacteristic | None = None
    otherCharacteristics: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None

class MedicinalProductPackagedBatchIdentifier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    outerPackaging: fhir_types.Identifier
    immediatePackaging: fhir_types.Identifier | None = None
class MedicinalProductPackagedPackageItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    quantity: fhir_types.Quantity
    material: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    alternateMaterial: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    device: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    manufacturedItem: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    packageItem: Annotated[list[MedicinalProductPackagedPackageItem], Field(min_length=1)] | None = None
    physicalCharacteristics: fhir_types.ProdCharacteristic | None = None
    otherCharacteristics: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    shelfLifeStorage: Annotated[list[fhir_types.ProductShelfLife], Field(min_length=1)] | None = None
    manufacturer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class MedicinalProductPackaged(DomainResourceR4):
    resourceType: Literal['MedicinalProductPackaged']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    legalStatusOfSupply: fhir_types.CodeableConcept | None = None
    marketingStatus: Annotated[list[fhir_types.MarketingStatus], Field(min_length=1)] | None = None
    marketingAuthorization: fhir_types.Reference | None = None
    manufacturer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    batchIdentifier: Annotated[list[MedicinalProductPackagedBatchIdentifier], Field(min_length=1)] | None = None
    packageItem: Annotated[list[MedicinalProductPackagedPackageItem], Field(min_length=1)]

class MedicinalProductPharmaceuticalCharacteristics(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    status: fhir_types.CodeableConcept | None = None
class MedicinalProductPharmaceuticalRouteOfAdministrationTargetSpeciesWithdrawalPeriod(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    tissue: fhir_types.CodeableConcept
    value: fhir_types.Quantity
    supportingInformation: StrictStr | None = None
class MedicinalProductPharmaceuticalRouteOfAdministrationTargetSpecies(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    withdrawalPeriod: Annotated[list[MedicinalProductPharmaceuticalRouteOfAdministrationTargetSpeciesWithdrawalPeriod], Field(min_length=1)] | None = None
class MedicinalProductPharmaceuticalRouteOfAdministration(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    firstDose: fhir_types.Quantity | None = None
    maxSingleDose: fhir_types.Quantity | None = None
    maxDosePerDay: fhir_types.Quantity | None = None
    maxDosePerTreatmentPeriod: fhir_types.Ratio | None = None
    maxTreatmentPeriod: fhir_types.Duration | None = None
    targetSpecies: Annotated[list[MedicinalProductPharmaceuticalRouteOfAdministrationTargetSpecies], Field(min_length=1)] | None = None
class MedicinalProductPharmaceutical(DomainResourceR4):
    resourceType: Literal['MedicinalProductPharmaceutical']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    administrableDoseForm: fhir_types.CodeableConcept
    unitOfPresentation: fhir_types.CodeableConcept | None = None
    ingredient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    device: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    characteristics: Annotated[list[MedicinalProductPharmaceuticalCharacteristics], Field(min_length=1)] | None = None
    routeOfAdministration: Annotated[list[MedicinalProductPharmaceuticalRouteOfAdministration], Field(min_length=1)]

class MedicinalProductUndesirableEffect(DomainResourceR4):
    resourceType: Literal['MedicinalProductUndesirableEffect']
    subject: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    symptomConditionEffect: fhir_types.CodeableConcept | None = None
    classification: fhir_types.CodeableConcept | None = None
    frequencyOfOccurrence: fhir_types.CodeableConcept | None = None
    population: Annotated[list[fhir_types.Population], Field(min_length=1)] | None = None

class MessageDefinitionFocus(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    profile: StrictStr | None = None
    min: FHIRUnsignedInt
    max: StrictStr | None = None
class MessageDefinitionAllowedResponse(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    message: StrictStr
    situation: StrictStr | None = None
class MessageDefinition(DomainResourceR4):
    resourceType: Literal['MessageDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    replaces: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    base: StrictStr | None = None
    parent: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    eventCoding: fhir_types.Coding | None = None
    eventUri: StrictStr | None = None
    category: Literal['consequence', 'currency', 'notification'] | None = None
    focus: Annotated[list[MessageDefinitionFocus], Field(min_length=1)] | None = None
    responseRequired: Literal['always', 'never', 'on-error', 'on-success'] | None = None
    allowedResponse: Annotated[list[MessageDefinitionAllowedResponse], Field(min_length=1)] | None = None
    graph: Annotated[list[StrictStr], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MessageDefinition':
        _present = sum(1 for _f in ('eventCoding', 'eventUri',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('event[x] requires exactly one value')
        return self

class MessageHeaderDestination(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    target: fhir_types.Reference | None = None
    endpoint: StrictStr
    receiver: fhir_types.Reference | None = None
class MessageHeaderSource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    software: StrictStr | None = None
    version: StrictStr | None = None
    contact: fhir_types.ContactPoint | None = None
    endpoint: StrictStr
class MessageHeaderResponse(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: FHIRId
    code: Literal['fatal-error', 'ok', 'transient-error']
    details: fhir_types.Reference | None = None
class MessageHeader(DomainResourceR4):
    resourceType: Literal['MessageHeader']
    eventCoding: fhir_types.Coding | None = None
    eventUri: StrictStr | None = None
    destination: Annotated[list[MessageHeaderDestination], Field(min_length=1)] | None = None
    sender: fhir_types.Reference | None = None
    enterer: fhir_types.Reference | None = None
    author: fhir_types.Reference | None = None
    source: MessageHeaderSource
    responsible: fhir_types.Reference | None = None
    reason: fhir_types.CodeableConcept | None = None
    response: MessageHeaderResponse | None = None
    focus: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    definition: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'MessageHeader':
        _present = sum(1 for _f in ('eventCoding', 'eventUri',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('event[x] requires exactly one value')
        return self

class MolecularSequenceReferenceSeq(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    chromosome: fhir_types.CodeableConcept | None = None
    genomeBuild: StrictStr | None = None
    orientation: Literal['antisense', 'sense'] | None = None
    referenceSeqId: fhir_types.CodeableConcept | None = None
    referenceSeqPointer: fhir_types.Reference | None = None
    referenceSeqString: StrictStr | None = None
    strand: Literal['crick', 'watson'] | None = None
    windowStart: FHIRInteger | None = None
    windowEnd: FHIRInteger | None = None
class MolecularSequenceVariant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    start: FHIRInteger | None = None
    end: FHIRInteger | None = None
    observedAllele: StrictStr | None = None
    referenceAllele: StrictStr | None = None
    cigar: StrictStr | None = None
    variantPointer: fhir_types.Reference | None = None
class MolecularSequenceQualityRoc(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    score: Annotated[list[FHIRInteger], Field(min_length=1)] | None = None
    numTP: Annotated[list[FHIRInteger], Field(min_length=1)] | None = None
    numFP: Annotated[list[FHIRInteger], Field(min_length=1)] | None = None
    numFN: Annotated[list[FHIRInteger], Field(min_length=1)] | None = None
    precision: Annotated[list[FHIRDecimal], Field(min_length=1)] | None = None
    sensitivity: Annotated[list[FHIRDecimal], Field(min_length=1)] | None = None
    fMeasure: Annotated[list[FHIRDecimal], Field(min_length=1)] | None = None
class MolecularSequenceQuality(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['indel', 'snp', 'unknown']
    standardSequence: fhir_types.CodeableConcept | None = None
    start: FHIRInteger | None = None
    end: FHIRInteger | None = None
    score: fhir_types.Quantity | None = None
    method: fhir_types.CodeableConcept | None = None
    truthTP: FHIRDecimal | None = None
    queryTP: FHIRDecimal | None = None
    truthFN: FHIRDecimal | None = None
    queryFP: FHIRDecimal | None = None
    gtFP: FHIRDecimal | None = None
    precision: FHIRDecimal | None = None
    recall: FHIRDecimal | None = None
    fScore: FHIRDecimal | None = None
    roc: MolecularSequenceQualityRoc | None = None
class MolecularSequenceRepository(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['directlink', 'login', 'oauth', 'openapi', 'other']
    url: StrictStr | None = None
    name: StrictStr | None = None
    datasetId: StrictStr | None = None
    variantsetId: StrictStr | None = None
    readsetId: StrictStr | None = None
class MolecularSequenceStructureVariantOuter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    start: FHIRInteger | None = None
    end: FHIRInteger | None = None
class MolecularSequenceStructureVariantInner(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    start: FHIRInteger | None = None
    end: FHIRInteger | None = None
class MolecularSequenceStructureVariant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    variantType: fhir_types.CodeableConcept | None = None
    exact: StrictBool | None = None
    length: FHIRInteger | None = None
    outer: MolecularSequenceStructureVariantOuter | None = None
    inner: MolecularSequenceStructureVariantInner | None = None
class MolecularSequence(DomainResourceR4):
    resourceType: Literal['MolecularSequence']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    type: Literal['aa', 'dna', 'rna'] | None = None
    coordinateSystem: FHIRInteger
    patient: fhir_types.Reference | None = None
    specimen: fhir_types.Reference | None = None
    device: fhir_types.Reference | None = None
    performer: fhir_types.Reference | None = None
    quantity: fhir_types.Quantity | None = None
    referenceSeq: MolecularSequenceReferenceSeq | None = None
    variant: Annotated[list[MolecularSequenceVariant], Field(min_length=1)] | None = None
    observedSeq: StrictStr | None = None
    quality: Annotated[list[MolecularSequenceQuality], Field(min_length=1)] | None = None
    readCoverage: FHIRInteger | None = None
    repository: Annotated[list[MolecularSequenceRepository], Field(min_length=1)] | None = None
    pointer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    structureVariant: Annotated[list[MolecularSequenceStructureVariant], Field(min_length=1)] | None = None

class NamingSystemUniqueId(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['oid', 'other', 'uri', 'uuid']
    value: StrictStr
    preferred: StrictBool | None = None
    comment: StrictStr | None = None
    period: fhir_types.Period | None = None
class NamingSystem(DomainResourceR4):
    resourceType: Literal['NamingSystem']
    name: StrictStr
    status: Literal['active', 'draft', 'retired', 'unknown']
    kind: Literal['codesystem', 'identifier', 'root']
    date: FHIRDateTime
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    responsible: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    usage: StrictStr | None = None
    uniqueId: Annotated[list[NamingSystemUniqueId], Field(min_length=1)]

class NutritionOrderOralDietNutrient(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifier: fhir_types.CodeableConcept | None = None
    amount: fhir_types.SimpleQuantity | None = None
class NutritionOrderOralDietTexture(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifier: fhir_types.CodeableConcept | None = None
    foodType: fhir_types.CodeableConcept | None = None
class NutritionOrderOralDiet(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    schedule: Annotated[list[fhir_types.Timing], Field(min_length=1)] | None = None
    nutrient: Annotated[list[NutritionOrderOralDietNutrient], Field(min_length=1)] | None = None
    texture: Annotated[list[NutritionOrderOralDietTexture], Field(min_length=1)] | None = None
    fluidConsistencyType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    instruction: StrictStr | None = None
class NutritionOrderSupplement(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    productName: StrictStr | None = None
    schedule: Annotated[list[fhir_types.Timing], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    instruction: StrictStr | None = None
class NutritionOrderEnteralFormulaAdministration(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    schedule: fhir_types.Timing | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    rateQuantity: fhir_types.SimpleQuantity | None = None
    rateRatio: fhir_types.Ratio | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'NutritionOrderEnteralFormulaAdministration':
        _present = sum(1 for _f in ('rateQuantity', 'rateRatio',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('rate[x] allows at most one value')
        return self
class NutritionOrderEnteralFormula(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    baseFormulaType: fhir_types.CodeableConcept | None = None
    baseFormulaProductName: StrictStr | None = None
    additiveType: fhir_types.CodeableConcept | None = None
    additiveProductName: StrictStr | None = None
    caloricDensity: fhir_types.SimpleQuantity | None = None
    routeofAdministration: fhir_types.CodeableConcept | None = None
    administration: Annotated[list[NutritionOrderEnteralFormulaAdministration], Field(min_length=1)] | None = None
    maxVolumeToDeliver: fhir_types.SimpleQuantity | None = None
    administrationInstruction: StrictStr | None = None
class NutritionOrder(DomainResourceR4):
    resourceType: Literal['NutritionOrder']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiates: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown']
    intent: Literal['directive', 'filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order']
    patient: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    dateTime: FHIRDateTime
    orderer: fhir_types.Reference | None = None
    allergyIntolerance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    foodPreferenceModifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    excludeFoodModifier: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    oralDiet: NutritionOrderOralDiet | None = None
    supplement: Annotated[list[NutritionOrderSupplement], Field(min_length=1)] | None = None
    enteralFormula: NutritionOrderEnteralFormula | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class ObservationReferenceRange(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    low: fhir_types.SimpleQuantity | None = None
    high: fhir_types.SimpleQuantity | None = None
    type: fhir_types.CodeableConcept | None = None
    appliesTo: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    age: fhir_types.Range | None = None
    text: StrictStr | None = None
class ObservationComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    valueQuantity: fhir_types.Quantity | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueString: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: FHIRInteger | None = None
    valueRange: fhir_types.Range | None = None
    valueRatio: fhir_types.Ratio | None = None
    valueSampledData: fhir_types.SampledData | None = None
    valueTime: FHIRTime | None = None
    valueDateTime: FHIRDateTime | None = None
    valuePeriod: fhir_types.Period | None = None
    dataAbsentReason: fhir_types.CodeableConcept | None = None
    interpretation: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    referenceRange: Annotated[list[ObservationReferenceRange], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ObservationComponent':
        _present = sum(1 for _f in ('valueQuantity', 'valueCodeableConcept', 'valueString', 'valueBoolean', 'valueInteger', 'valueRange', 'valueRatio', 'valueSampledData', 'valueTime', 'valueDateTime', 'valuePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class Observation(DomainResourceR4):
    resourceType: Literal['Observation']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['amended', 'cancelled', 'corrected', 'entered-in-error', 'final', 'preliminary', 'registered', 'unknown']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    subject: fhir_types.Reference | None = None
    focus: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    encounter: fhir_types.Reference | None = None
    effectiveDateTime: FHIRDateTime | None = None
    effectivePeriod: fhir_types.Period | None = None
    effectiveTiming: fhir_types.Timing | None = None
    effectiveInstant: FHIRInstant | None = None
    issued: FHIRInstant | None = None
    performer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueString: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: FHIRInteger | None = None
    valueRange: fhir_types.Range | None = None
    valueRatio: fhir_types.Ratio | None = None
    valueSampledData: fhir_types.SampledData | None = None
    valueTime: FHIRTime | None = None
    valueDateTime: FHIRDateTime | None = None
    valuePeriod: fhir_types.Period | None = None
    dataAbsentReason: fhir_types.CodeableConcept | None = None
    interpretation: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    method: fhir_types.CodeableConcept | None = None
    specimen: fhir_types.Reference | None = None
    device: fhir_types.Reference | None = None
    referenceRange: Annotated[list[ObservationReferenceRange], Field(min_length=1)] | None = None
    hasMember: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    derivedFrom: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    component: Annotated[list[ObservationComponent], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Observation':
        _present = sum(1 for _f in ('effectiveDateTime', 'effectivePeriod', 'effectiveTiming', 'effectiveInstant',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('effective[x] allows at most one value')
        _present = sum(1 for _f in ('valueQuantity', 'valueCodeableConcept', 'valueString', 'valueBoolean', 'valueInteger', 'valueRange', 'valueRatio', 'valueSampledData', 'valueTime', 'valueDateTime', 'valuePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self

class ObservationDefinitionQuantitativeDetails(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    customaryUnit: fhir_types.CodeableConcept | None = None
    unit: fhir_types.CodeableConcept | None = None
    conversionFactor: FHIRDecimal | None = None
    decimalPrecision: FHIRInteger | None = None
class ObservationDefinitionQualifiedInterval(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: Literal['absolute', 'critical', 'reference'] | None = None
    range: fhir_types.Range | None = None
    context: fhir_types.CodeableConcept | None = None
    appliesTo: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    age: fhir_types.Range | None = None
    gestationalAge: fhir_types.Range | None = None
    condition: StrictStr | None = None
class ObservationDefinition(DomainResourceR4):
    resourceType: Literal['ObservationDefinition']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    permittedDataType: Annotated[list[Literal['CodeableConcept', 'Period', 'Quantity', 'Range', 'Ratio', 'SampledData', 'boolean', 'dateTime', 'integer', 'string', 'time']], Field(min_length=1)] | None = None
    multipleResultsAllowed: StrictBool | None = None
    method: fhir_types.CodeableConcept | None = None
    preferredReportName: StrictStr | None = None
    quantitativeDetails: ObservationDefinitionQuantitativeDetails | None = None
    qualifiedInterval: Annotated[list[ObservationDefinitionQualifiedInterval], Field(min_length=1)] | None = None
    validCodedValueSet: fhir_types.Reference | None = None
    normalCodedValueSet: fhir_types.Reference | None = None
    abnormalCodedValueSet: fhir_types.Reference | None = None
    criticalCodedValueSet: fhir_types.Reference | None = None

class OperationDefinitionParameterBinding(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    strength: Literal['example', 'extensible', 'preferred', 'required']
    valueSet: StrictStr
class OperationDefinitionParameterReferencedFrom(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    source: StrictStr
    sourceId: StrictStr | None = None
class OperationDefinitionParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRCode
    use: Literal['in', 'out']
    min: FHIRInteger
    max: StrictStr
    documentation: StrictStr | None = None
    type: FHIRCode | None = None
    targetProfile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    searchType: Literal['composite', 'date', 'number', 'quantity', 'reference', 'special', 'string', 'token', 'uri'] | None = None
    binding: OperationDefinitionParameterBinding | None = None
    referencedFrom: Annotated[list[OperationDefinitionParameterReferencedFrom], Field(min_length=1)] | None = None
    part: Annotated[list[OperationDefinitionParameter], Field(min_length=1)] | None = None
class OperationDefinitionOverload(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    parameterName: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    comment: StrictStr | None = None
class OperationDefinition(DomainResourceR4):
    resourceType: Literal['OperationDefinition']
    url: StrictStr | None = None
    version: StrictStr | None = None
    name: StrictStr
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    kind: Literal['operation', 'query']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    affectsState: StrictBool | None = None
    code: FHIRCode
    comment: StrictStr | None = None
    base: StrictStr | None = None
    resource: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    system: StrictBool
    type: StrictBool
    instance: StrictBool
    inputProfile: StrictStr | None = None
    outputProfile: StrictStr | None = None
    parameter: Annotated[list[OperationDefinitionParameter], Field(min_length=1)] | None = None
    overload: Annotated[list[OperationDefinitionOverload], Field(min_length=1)] | None = None

class OperationOutcomeIssue(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    severity: Literal['error', 'fatal', 'information', 'warning']
    code: Literal['business-rule', 'code-invalid', 'conflict', 'deleted', 'duplicate', 'exception', 'expired', 'extension', 'forbidden', 'incomplete', 'informational', 'invalid', 'invariant', 'lock-error', 'login', 'multiple-matches', 'no-store', 'not-found', 'not-supported', 'processing', 'required', 'security', 'structure', 'suppressed', 'throttled', 'timeout', 'too-costly', 'too-long', 'transient', 'unknown', 'value']
    details: fhir_types.CodeableConcept | None = None
    diagnostics: StrictStr | None = None
    location: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    expression: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class OperationOutcome(DomainResourceR4):
    resourceType: Literal['OperationOutcome']
    issue: Annotated[list[OperationOutcomeIssue], Field(min_length=1)]

class OrganizationContact(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    purpose: fhir_types.CodeableConcept | None = None
    name: fhir_types.HumanName | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: fhir_types.Address | None = None
class Organization(DomainResourceR4):
    resourceType: Literal['Organization']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    alias: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: Annotated[list[fhir_types.Address], Field(min_length=1)] | None = None
    partOf: fhir_types.Reference | None = None
    contact: Annotated[list[OrganizationContact], Field(min_length=1)] | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class OrganizationAffiliation(DomainResourceR4):
    resourceType: Literal['OrganizationAffiliation']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    period: fhir_types.Period | None = None
    organization: fhir_types.Reference | None = None
    participatingOrganization: fhir_types.Reference | None = None
    network: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    location: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    healthcareService: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class ParametersParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    valueBase64Binary: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueCanonical: StrictStr | None = None
    valueCode: FHIRCode | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueDecimal: FHIRDecimal | None = None
    valueId: FHIRId | None = None
    valueInstant: FHIRInstant | None = None
    valueInteger: FHIRInteger | None = None
    valueMarkdown: StrictStr | None = None
    valueOid: StrictStr | None = None
    valuePositiveInt: FHIRPositiveInt | None = None
    valueString: StrictStr | None = None
    valueTime: FHIRTime | None = None
    valueUnsignedInt: FHIRUnsignedInt | None = None
    valueUri: StrictStr | None = None
    valueUrl: StrictStr | None = None
    valueUuid: StrictStr | None = None
    valueAddress: fhir_types.Address | None = None
    valueAge: fhir_types.Age | None = None
    valueAnnotation: fhir_types.Annotation | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueCoding: fhir_types.Coding | None = None
    valueContactPoint: fhir_types.ContactPoint | None = None
    valueCount: fhir_types.Count | None = None
    valueDistance: fhir_types.Distance | None = None
    valueDuration: fhir_types.Duration | None = None
    valueHumanName: fhir_types.HumanName | None = None
    valueIdentifier: fhir_types.Identifier | None = None
    valueMoney: fhir_types.Money | None = None
    valuePeriod: fhir_types.Period | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueRatio: fhir_types.Ratio | None = None
    valueReference: fhir_types.Reference | None = None
    valueSampledData: fhir_types.SampledData | None = None
    valueSignature: fhir_types.Signature | None = None
    valueTiming: fhir_types.Timing | None = None
    valueContactDetail: fhir_types.ContactDetail | None = None
    valueContributor: fhir_types.Contributor | None = None
    valueDataRequirement: fhir_types.DataRequirement | None = None
    valueExpression: fhir_types.Expression | None = None
    valueParameterDefinition: fhir_types.ParameterDefinition | None = None
    valueRelatedArtifact: fhir_types.RelatedArtifact | None = None
    valueTriggerDefinition: fhir_types.TriggerDefinition | None = None
    valueUsageContext: fhir_types.UsageContext | None = None
    valueDosage: fhir_types.Dosage | None = None
    valueMeta: fhir_types.Meta | None = None
    resource: dict[str, Any] | None = None
    part: Annotated[list[ParametersParameter], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ParametersParameter':
        _present = sum(1 for _f in ('valueBase64Binary', 'valueBoolean', 'valueCanonical', 'valueCode', 'valueDate', 'valueDateTime', 'valueDecimal', 'valueId', 'valueInstant', 'valueInteger', 'valueMarkdown', 'valueOid', 'valuePositiveInt', 'valueString', 'valueTime', 'valueUnsignedInt', 'valueUri', 'valueUrl', 'valueUuid', 'valueAddress', 'valueAge', 'valueAnnotation', 'valueAttachment', 'valueCodeableConcept', 'valueCoding', 'valueContactPoint', 'valueCount', 'valueDistance', 'valueDuration', 'valueHumanName', 'valueIdentifier', 'valueMoney', 'valuePeriod', 'valueQuantity', 'valueRange', 'valueRatio', 'valueReference', 'valueSampledData', 'valueSignature', 'valueTiming', 'valueContactDetail', 'valueContributor', 'valueDataRequirement', 'valueExpression', 'valueParameterDefinition', 'valueRelatedArtifact', 'valueTriggerDefinition', 'valueUsageContext', 'valueDosage', 'valueMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class Parameters(DomainResourceR4):
    resourceType: Literal['Parameters']
    parameter: Annotated[list[ParametersParameter], Field(min_length=1)] | None = None

class PatientContact(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    relationship: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    name: fhir_types.HumanName | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: fhir_types.Address | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    organization: fhir_types.Reference | None = None
    period: fhir_types.Period | None = None
class PatientCommunication(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    language: fhir_types.CodeableConcept
    preferred: StrictBool | None = None
class PatientLink(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    other: fhir_types.Reference
    type: Literal['refer', 'replaced-by', 'replaces', 'seealso']
class Patient(DomainResourceR4):
    resourceType: Literal['Patient']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    name: Annotated[list[fhir_types.HumanName], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    birthDate: FHIRDate | None = None
    deceasedBoolean: StrictBool | None = None
    deceasedDateTime: FHIRDateTime | None = None
    address: Annotated[list[fhir_types.Address], Field(min_length=1)] | None = None
    maritalStatus: fhir_types.CodeableConcept | None = None
    multipleBirthBoolean: StrictBool | None = None
    multipleBirthInteger: FHIRInteger | None = None
    photo: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None
    contact: Annotated[list[PatientContact], Field(min_length=1)] | None = None
    communication: Annotated[list[PatientCommunication], Field(min_length=1)] | None = None
    generalPractitioner: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    managingOrganization: fhir_types.Reference | None = None
    link: Annotated[list[PatientLink], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Patient':
        _present = sum(1 for _f in ('deceasedBoolean', 'deceasedDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('deceased[x] allows at most one value')
        _present = sum(1 for _f in ('multipleBirthBoolean', 'multipleBirthInteger',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('multipleBirth[x] allows at most one value')
        return self

class PaymentNotice(DomainResourceR4):
    resourceType: Literal['PaymentNotice']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    request: fhir_types.Reference | None = None
    response: fhir_types.Reference | None = None
    created: FHIRDateTime
    provider: fhir_types.Reference | None = None
    payment: fhir_types.Reference
    paymentDate: FHIRDate | None = None
    payee: fhir_types.Reference | None = None
    recipient: fhir_types.Reference
    amount: fhir_types.Money
    paymentStatus: fhir_types.CodeableConcept | None = None

class PaymentReconciliationDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    predecessor: fhir_types.Identifier | None = None
    type: fhir_types.CodeableConcept
    request: fhir_types.Reference | None = None
    submitter: fhir_types.Reference | None = None
    response: fhir_types.Reference | None = None
    date: FHIRDate | None = None
    responsible: fhir_types.Reference | None = None
    payee: fhir_types.Reference | None = None
    amount: fhir_types.Money | None = None
class PaymentReconciliationProcessNote(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['display', 'print', 'printoper'] | None = None
    text: StrictStr | None = None
class PaymentReconciliation(DomainResourceR4):
    resourceType: Literal['PaymentReconciliation']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    period: fhir_types.Period | None = None
    created: FHIRDateTime
    paymentIssuer: fhir_types.Reference | None = None
    request: fhir_types.Reference | None = None
    requestor: fhir_types.Reference | None = None
    outcome: Literal['complete', 'error', 'partial', 'queued'] | None = None
    disposition: StrictStr | None = None
    paymentDate: FHIRDate
    paymentAmount: fhir_types.Money
    paymentIdentifier: fhir_types.Identifier | None = None
    detail: Annotated[list[PaymentReconciliationDetail], Field(min_length=1)] | None = None
    formCode: fhir_types.CodeableConcept | None = None
    processNote: Annotated[list[PaymentReconciliationProcessNote], Field(min_length=1)] | None = None

class PersonLink(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    target: fhir_types.Reference
    assurance: Literal['level1', 'level2', 'level3', 'level4'] | None = None
class Person(DomainResourceR4):
    resourceType: Literal['Person']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    name: Annotated[list[fhir_types.HumanName], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    birthDate: FHIRDate | None = None
    address: Annotated[list[fhir_types.Address], Field(min_length=1)] | None = None
    photo: fhir_types.Attachment | None = None
    managingOrganization: fhir_types.Reference | None = None
    active: StrictBool | None = None
    link: Annotated[list[PersonLink], Field(min_length=1)] | None = None

class PlanDefinitionGoalTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    measure: fhir_types.CodeableConcept | None = None
    detailQuantity: fhir_types.Quantity | None = None
    detailRange: fhir_types.Range | None = None
    detailCodeableConcept: fhir_types.CodeableConcept | None = None
    due: fhir_types.Duration | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'PlanDefinitionGoalTarget':
        _present = sum(1 for _f in ('detailQuantity', 'detailRange', 'detailCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('detail[x] allows at most one value')
        return self
class PlanDefinitionGoal(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    description: fhir_types.CodeableConcept
    priority: fhir_types.CodeableConcept | None = None
    start: fhir_types.CodeableConcept | None = None
    addresses: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    documentation: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    target: Annotated[list[PlanDefinitionGoalTarget], Field(min_length=1)] | None = None
class PlanDefinitionActionCondition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    kind: Literal['applicability', 'start', 'stop']
    expression: fhir_types.Expression | None = None
class PlanDefinitionActionRelatedAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    actionId: FHIRId
    relationship: Literal['after', 'after-end', 'after-start', 'before', 'before-end', 'before-start', 'concurrent', 'concurrent-with-end', 'concurrent-with-start']
    offsetDuration: fhir_types.Duration | None = None
    offsetRange: fhir_types.Range | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'PlanDefinitionActionRelatedAction':
        _present = sum(1 for _f in ('offsetDuration', 'offsetRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('offset[x] allows at most one value')
        return self
class PlanDefinitionActionParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['device', 'patient', 'practitioner', 'related-person']
    role: fhir_types.CodeableConcept | None = None
class PlanDefinitionActionDynamicValue(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    path: StrictStr | None = None
    expression: fhir_types.Expression | None = None
class PlanDefinitionAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    prefix: StrictStr | None = None
    title: StrictStr | None = None
    description: StrictStr | None = None
    textEquivalent: StrictStr | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    documentation: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    goalId: Annotated[list[FHIRId], Field(min_length=1)] | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    trigger: Annotated[list[fhir_types.TriggerDefinition], Field(min_length=1)] | None = None
    condition: Annotated[list[PlanDefinitionActionCondition], Field(min_length=1)] | None = None
    input: Annotated[list[fhir_types.DataRequirement], Field(min_length=1)] | None = None
    output: Annotated[list[fhir_types.DataRequirement], Field(min_length=1)] | None = None
    relatedAction: Annotated[list[PlanDefinitionActionRelatedAction], Field(min_length=1)] | None = None
    timingDateTime: FHIRDateTime | None = None
    timingAge: fhir_types.Age | None = None
    timingPeriod: fhir_types.Period | None = None
    timingDuration: fhir_types.Duration | None = None
    timingRange: fhir_types.Range | None = None
    timingTiming: fhir_types.Timing | None = None
    participant: Annotated[list[PlanDefinitionActionParticipant], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    groupingBehavior: Literal['logical-group', 'sentence-group', 'visual-group'] | None = None
    selectionBehavior: Literal['all', 'all-or-none', 'any', 'at-most-one', 'exactly-one', 'one-or-more'] | None = None
    requiredBehavior: Literal['could', 'must', 'must-unless-documented'] | None = None
    precheckBehavior: Literal['no', 'yes'] | None = None
    cardinalityBehavior: Literal['multiple', 'single'] | None = None
    definitionCanonical: StrictStr | None = None
    definitionUri: StrictStr | None = None
    transform: StrictStr | None = None
    dynamicValue: Annotated[list[PlanDefinitionActionDynamicValue], Field(min_length=1)] | None = None
    action: Annotated[list[PlanDefinitionAction], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'PlanDefinitionAction':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        _present = sum(1 for _f in ('timingDateTime', 'timingAge', 'timingPeriod', 'timingDuration', 'timingRange', 'timingTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        _present = sum(1 for _f in ('definitionCanonical', 'definitionUri',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('definition[x] allows at most one value')
        return self
class PlanDefinition(DomainResourceR4):
    resourceType: Literal['PlanDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    subtitle: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    library: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    goal: Annotated[list[PlanDefinitionGoal], Field(min_length=1)] | None = None
    action: Annotated[list[PlanDefinitionAction], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'PlanDefinition':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class PractitionerQualification(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    period: fhir_types.Period | None = None
    issuer: fhir_types.Reference | None = None
class Practitioner(DomainResourceR4):
    resourceType: Literal['Practitioner']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    name: Annotated[list[fhir_types.HumanName], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    address: Annotated[list[fhir_types.Address], Field(min_length=1)] | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    birthDate: FHIRDate | None = None
    photo: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None
    qualification: Annotated[list[PractitionerQualification], Field(min_length=1)] | None = None
    communication: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None

class PractitionerRoleAvailableTime(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    daysOfWeek: Annotated[list[Literal['fri', 'mon', 'sat', 'sun', 'thu', 'tue', 'wed']], Field(min_length=1)] | None = None
    allDay: StrictBool | None = None
    availableStartTime: FHIRTime | None = None
    availableEndTime: FHIRTime | None = None
class PractitionerRoleNotAvailable(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr
    during: fhir_types.Period | None = None
class PractitionerRole(DomainResourceR4):
    resourceType: Literal['PractitionerRole']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    period: fhir_types.Period | None = None
    practitioner: fhir_types.Reference | None = None
    organization: fhir_types.Reference | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    location: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    healthcareService: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    availableTime: Annotated[list[PractitionerRoleAvailableTime], Field(min_length=1)] | None = None
    notAvailable: Annotated[list[PractitionerRoleNotAvailable], Field(min_length=1)] | None = None
    availabilityExceptions: StrictStr | None = None
    endpoint: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

class ProcedurePerformer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    function: fhir_types.CodeableConcept | None = None
    actor: fhir_types.Reference
    onBehalfOf: fhir_types.Reference | None = None
class ProcedureFocalDevice(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: fhir_types.CodeableConcept | None = None
    manipulated: fhir_types.Reference
class Procedure(DomainResourceR4):
    resourceType: Literal['Procedure']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress', 'not-done', 'on-hold', 'preparation', 'stopped', 'unknown']
    statusReason: fhir_types.CodeableConcept | None = None
    category: fhir_types.CodeableConcept | None = None
    code: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    performedDateTime: FHIRDateTime | None = None
    performedPeriod: fhir_types.Period | None = None
    performedString: StrictStr | None = None
    performedAge: fhir_types.Age | None = None
    performedRange: fhir_types.Range | None = None
    recorder: fhir_types.Reference | None = None
    asserter: fhir_types.Reference | None = None
    performer: Annotated[list[ProcedurePerformer], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    outcome: fhir_types.CodeableConcept | None = None
    report: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    complication: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    complicationDetail: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    followUp: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    focalDevice: Annotated[list[ProcedureFocalDevice], Field(min_length=1)] | None = None
    usedReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    usedCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Procedure':
        _present = sum(1 for _f in ('performedDateTime', 'performedPeriod', 'performedString', 'performedAge', 'performedRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('performed[x] allows at most one value')
        return self

class ProvenanceAgent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    role: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    who: fhir_types.Reference
    onBehalfOf: fhir_types.Reference | None = None
class ProvenanceEntity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    role: Literal['derivation', 'quotation', 'removal', 'revision', 'source']
    what: fhir_types.Reference
    agent: Annotated[list[ProvenanceAgent], Field(min_length=1)] | None = None
class Provenance(DomainResourceR4):
    resourceType: Literal['Provenance']
    target: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    occurredPeriod: fhir_types.Period | None = None
    occurredDateTime: FHIRDateTime | None = None
    recorded: FHIRInstant
    policy: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    location: fhir_types.Reference | None = None
    reason: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    activity: fhir_types.CodeableConcept | None = None
    agent: Annotated[list[ProvenanceAgent], Field(min_length=1)]
    entity: Annotated[list[ProvenanceEntity], Field(min_length=1)] | None = None
    signature: Annotated[list[fhir_types.Signature], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Provenance':
        _present = sum(1 for _f in ('occurredPeriod', 'occurredDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurred[x] allows at most one value')
        return self

class QuestionnaireItemEnableWhen(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    question: StrictStr
    operator: Literal['!=', '<', '<=', '=', '>', '>=', 'exists']
    answerBoolean: StrictBool | None = None
    answerDecimal: FHIRDecimal | None = None
    answerInteger: FHIRInteger | None = None
    answerDate: FHIRDate | None = None
    answerDateTime: FHIRDateTime | None = None
    answerTime: FHIRTime | None = None
    answerString: StrictStr | None = None
    answerCoding: fhir_types.Coding | None = None
    answerQuantity: fhir_types.Quantity | None = None
    answerReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'QuestionnaireItemEnableWhen':
        _present = sum(1 for _f in ('answerBoolean', 'answerDecimal', 'answerInteger', 'answerDate', 'answerDateTime', 'answerTime', 'answerString', 'answerCoding', 'answerQuantity', 'answerReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('answer[x] requires exactly one value')
        return self
class QuestionnaireItemAnswerOption(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    valueInteger: FHIRInteger | None = None
    valueDate: FHIRDate | None = None
    valueTime: FHIRTime | None = None
    valueString: StrictStr | None = None
    valueCoding: fhir_types.Coding | None = None
    valueReference: fhir_types.Reference | None = None
    initialSelected: StrictBool | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'QuestionnaireItemAnswerOption':
        _present = sum(1 for _f in ('valueInteger', 'valueDate', 'valueTime', 'valueString', 'valueCoding', 'valueReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class QuestionnaireItemInitial(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    valueBoolean: StrictBool | None = None
    valueDecimal: FHIRDecimal | None = None
    valueInteger: FHIRInteger | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueTime: FHIRTime | None = None
    valueString: StrictStr | None = None
    valueUri: StrictStr | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCoding: fhir_types.Coding | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'QuestionnaireItemInitial':
        _present = sum(1 for _f in ('valueBoolean', 'valueDecimal', 'valueInteger', 'valueDate', 'valueDateTime', 'valueTime', 'valueString', 'valueUri', 'valueAttachment', 'valueCoding', 'valueQuantity', 'valueReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class QuestionnaireItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    linkId: StrictStr
    definition: StrictStr | None = None
    code: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    prefix: StrictStr | None = None
    text: StrictStr | None = None
    type: Literal['attachment', 'boolean', 'choice', 'date', 'dateTime', 'decimal', 'display', 'group', 'integer', 'open-choice', 'quantity', 'question', 'reference', 'string', 'text', 'time', 'url']
    enableWhen: Annotated[list[QuestionnaireItemEnableWhen], Field(min_length=1)] | None = None
    enableBehavior: Literal['all', 'any'] | None = None
    required: StrictBool | None = None
    repeats: StrictBool | None = None
    readOnly: StrictBool | None = None
    maxLength: FHIRInteger | None = None
    answerValueSet: StrictStr | None = None
    answerOption: Annotated[list[QuestionnaireItemAnswerOption], Field(min_length=1)] | None = None
    initial: Annotated[list[QuestionnaireItemInitial], Field(min_length=1)] | None = None
    item: Annotated[list[QuestionnaireItem], Field(min_length=1)] | None = None
class Questionnaire(DomainResourceR4):
    resourceType: Literal['Questionnaire']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    derivedFrom: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectType: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    code: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    item: Annotated[list[QuestionnaireItem], Field(min_length=1)] | None = None

class QuestionnaireResponseItemAnswer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    valueBoolean: StrictBool | None = None
    valueDecimal: FHIRDecimal | None = None
    valueInteger: FHIRInteger | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueTime: FHIRTime | None = None
    valueString: StrictStr | None = None
    valueUri: StrictStr | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCoding: fhir_types.Coding | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueReference: fhir_types.Reference | None = None
    item: Annotated[list[QuestionnaireResponseItem], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'QuestionnaireResponseItemAnswer':
        _present = sum(1 for _f in ('valueBoolean', 'valueDecimal', 'valueInteger', 'valueDate', 'valueDateTime', 'valueTime', 'valueString', 'valueUri', 'valueAttachment', 'valueCoding', 'valueQuantity', 'valueReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class QuestionnaireResponseItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    linkId: StrictStr
    definition: StrictStr | None = None
    text: StrictStr | None = None
    answer: Annotated[list[QuestionnaireResponseItemAnswer], Field(min_length=1)] | None = None
    item: Annotated[list[QuestionnaireResponseItem], Field(min_length=1)] | None = None
class QuestionnaireResponse(DomainResourceR4):
    resourceType: Literal['QuestionnaireResponse']
    identifier: fhir_types.Identifier | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    questionnaire: StrictStr | None = None
    status: Literal['amended', 'completed', 'entered-in-error', 'in-progress', 'stopped']
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    authored: FHIRDateTime | None = None
    author: fhir_types.Reference | None = None
    source: fhir_types.Reference | None = None
    item: Annotated[list[QuestionnaireResponseItem], Field(min_length=1)] | None = None

class RelatedPersonCommunication(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    language: fhir_types.CodeableConcept
    preferred: StrictBool | None = None
class RelatedPerson(DomainResourceR4):
    resourceType: Literal['RelatedPerson']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    patient: fhir_types.Reference
    relationship: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    name: Annotated[list[fhir_types.HumanName], Field(min_length=1)] | None = None
    telecom: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    gender: Literal['female', 'male', 'other', 'unknown'] | None = None
    birthDate: FHIRDate | None = None
    address: Annotated[list[fhir_types.Address], Field(min_length=1)] | None = None
    photo: Annotated[list[fhir_types.Attachment], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    communication: Annotated[list[RelatedPersonCommunication], Field(min_length=1)] | None = None

class RequestGroupActionCondition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    kind: Literal['applicability', 'start', 'stop']
    expression: fhir_types.Expression | None = None
class RequestGroupActionRelatedAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    actionId: FHIRId
    relationship: Literal['after', 'after-end', 'after-start', 'before', 'before-end', 'before-start', 'concurrent', 'concurrent-with-end', 'concurrent-with-start']
    offsetDuration: fhir_types.Duration | None = None
    offsetRange: fhir_types.Range | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'RequestGroupActionRelatedAction':
        _present = sum(1 for _f in ('offsetDuration', 'offsetRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('offset[x] allows at most one value')
        return self
class RequestGroupAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    prefix: StrictStr | None = None
    title: StrictStr | None = None
    description: StrictStr | None = None
    textEquivalent: StrictStr | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    code: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    documentation: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    condition: Annotated[list[RequestGroupActionCondition], Field(min_length=1)] | None = None
    relatedAction: Annotated[list[RequestGroupActionRelatedAction], Field(min_length=1)] | None = None
    timingDateTime: FHIRDateTime | None = None
    timingAge: fhir_types.Age | None = None
    timingPeriod: fhir_types.Period | None = None
    timingDuration: fhir_types.Duration | None = None
    timingRange: fhir_types.Range | None = None
    timingTiming: fhir_types.Timing | None = None
    participant: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    groupingBehavior: Literal['logical-group', 'sentence-group', 'visual-group'] | None = None
    selectionBehavior: Literal['all', 'all-or-none', 'any', 'at-most-one', 'exactly-one', 'one-or-more'] | None = None
    requiredBehavior: Literal['could', 'must', 'must-unless-documented'] | None = None
    precheckBehavior: Literal['no', 'yes'] | None = None
    cardinalityBehavior: Literal['multiple', 'single'] | None = None
    resource: fhir_types.Reference | None = None
    action: Annotated[list[RequestGroupAction], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'RequestGroupAction':
        _present = sum(1 for _f in ('timingDateTime', 'timingAge', 'timingPeriod', 'timingDuration', 'timingRange', 'timingTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        return self
class RequestGroup(DomainResourceR4):
    resourceType: Literal['RequestGroup']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    replaces: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    groupIdentifier: fhir_types.Identifier | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown']
    intent: Literal['directive', 'filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order']
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    code: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    encounter: fhir_types.Reference | None = None
    authoredOn: FHIRDateTime | None = None
    author: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    action: Annotated[list[RequestGroupAction], Field(min_length=1)] | None = None

class ResearchDefinition(DomainResourceR4):
    resourceType: Literal['ResearchDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    shortTitle: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    comment: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    library: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    population: fhir_types.Reference
    exposure: fhir_types.Reference | None = None
    exposureAlternative: fhir_types.Reference | None = None
    outcome: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ResearchDefinition':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class ResearchElementDefinitionCharacteristic(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    definitionCodeableConcept: fhir_types.CodeableConcept | None = None
    definitionCanonical: StrictStr | None = None
    definitionExpression: fhir_types.Expression | None = None
    definitionDataRequirement: fhir_types.DataRequirement | None = None
    usageContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    exclude: StrictBool | None = None
    unitOfMeasure: fhir_types.CodeableConcept | None = None
    studyEffectiveDescription: StrictStr | None = None
    studyEffectiveDateTime: FHIRDateTime | None = None
    studyEffectivePeriod: fhir_types.Period | None = None
    studyEffectiveDuration: fhir_types.Duration | None = None
    studyEffectiveTiming: fhir_types.Timing | None = None
    studyEffectiveTimeFromStart: fhir_types.Duration | None = None
    studyEffectiveGroupMeasure: Literal['mean', 'mean-of-mean', 'mean-of-median', 'median', 'median-of-mean', 'median-of-median'] | None = None
    participantEffectiveDescription: StrictStr | None = None
    participantEffectiveDateTime: FHIRDateTime | None = None
    participantEffectivePeriod: fhir_types.Period | None = None
    participantEffectiveDuration: fhir_types.Duration | None = None
    participantEffectiveTiming: fhir_types.Timing | None = None
    participantEffectiveTimeFromStart: fhir_types.Duration | None = None
    participantEffectiveGroupMeasure: Literal['mean', 'mean-of-mean', 'mean-of-median', 'median', 'median-of-mean', 'median-of-median'] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ResearchElementDefinitionCharacteristic':
        _present = sum(1 for _f in ('definitionCodeableConcept', 'definitionCanonical', 'definitionExpression', 'definitionDataRequirement',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('definition[x] requires exactly one value')
        _present = sum(1 for _f in ('studyEffectiveDateTime', 'studyEffectivePeriod', 'studyEffectiveDuration', 'studyEffectiveTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('studyEffective[x] allows at most one value')
        _present = sum(1 for _f in ('participantEffectiveDateTime', 'participantEffectivePeriod', 'participantEffectiveDuration', 'participantEffectiveTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('participantEffective[x] allows at most one value')
        return self
class ResearchElementDefinition(DomainResourceR4):
    resourceType: Literal['ResearchElementDefinition']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    shortTitle: StrictStr | None = None
    subtitle: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    subjectCodeableConcept: fhir_types.CodeableConcept | None = None
    subjectReference: fhir_types.Reference | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    comment: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    usage: StrictStr | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    library: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    type: Literal['exposure', 'outcome', 'population']
    variableType: Literal['continuous', 'descriptive', 'dichotomous'] | None = None
    characteristic: Annotated[list[ResearchElementDefinitionCharacteristic], Field(min_length=1)]

    @model_validator(mode='after')
    def _check_choices(self) -> 'ResearchElementDefinition':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class ResearchStudyArm(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    type: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
class ResearchStudyObjective(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
class ResearchStudy(DomainResourceR4):
    resourceType: Literal['ResearchStudy']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    title: StrictStr | None = None
    protocol: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['active', 'administratively-completed', 'approved', 'closed-to-accrual', 'closed-to-accrual-and-intervention', 'completed', 'disapproved', 'in-review', 'temporarily-closed-to-accrual', 'temporarily-closed-to-accrual-and-intervention', 'withdrawn']
    primaryPurposeType: fhir_types.CodeableConcept | None = None
    phase: fhir_types.CodeableConcept | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    focus: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    condition: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    keyword: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    location: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    enrollment: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    period: fhir_types.Period | None = None
    sponsor: fhir_types.Reference | None = None
    principalInvestigator: fhir_types.Reference | None = None
    site: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    reasonStopped: fhir_types.CodeableConcept | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    arm: Annotated[list[ResearchStudyArm], Field(min_length=1)] | None = None
    objective: Annotated[list[ResearchStudyObjective], Field(min_length=1)] | None = None

class ResearchSubject(DomainResourceR4):
    resourceType: Literal['ResearchSubject']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['candidate', 'eligible', 'follow-up', 'ineligible', 'not-registered', 'off-study', 'on-study', 'on-study-intervention', 'on-study-observation', 'pending-on-study', 'potential-candidate', 'screening', 'withdrawn']
    period: fhir_types.Period | None = None
    study: fhir_types.Reference
    individual: fhir_types.Reference
    assignedArm: StrictStr | None = None
    actualArm: StrictStr | None = None
    consent: fhir_types.Reference | None = None

class RiskAssessmentPrediction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    outcome: fhir_types.CodeableConcept | None = None
    probabilityDecimal: FHIRDecimal | None = None
    probabilityRange: fhir_types.Range | None = None
    qualitativeRisk: fhir_types.CodeableConcept | None = None
    relativeRisk: FHIRDecimal | None = None
    whenPeriod: fhir_types.Period | None = None
    whenRange: fhir_types.Range | None = None
    rationale: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'RiskAssessmentPrediction':
        _present = sum(1 for _f in ('probabilityDecimal', 'probabilityRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('probability[x] allows at most one value')
        _present = sum(1 for _f in ('whenPeriod', 'whenRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('when[x] allows at most one value')
        return self
class RiskAssessment(DomainResourceR4):
    resourceType: Literal['RiskAssessment']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: fhir_types.Reference | None = None
    parent: fhir_types.Reference | None = None
    status: Literal['amended', 'cancelled', 'corrected', 'entered-in-error', 'final', 'preliminary', 'registered', 'unknown']
    method: fhir_types.CodeableConcept | None = None
    code: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    condition: fhir_types.Reference | None = None
    performer: fhir_types.Reference | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    basis: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    prediction: Annotated[list[RiskAssessmentPrediction], Field(min_length=1)] | None = None
    mitigation: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'RiskAssessment':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self

class RiskEvidenceSynthesisSampleSize(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    numberOfStudies: FHIRInteger | None = None
    numberOfParticipants: FHIRInteger | None = None
class RiskEvidenceSynthesisRiskEstimatePrecisionEstimate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    level: FHIRDecimal | None = None
    from_: FHIRDecimal | None = Field(default=None, alias='from')
    to: FHIRDecimal | None = None
class RiskEvidenceSynthesisRiskEstimate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    value: FHIRDecimal | None = None
    unitOfMeasure: fhir_types.CodeableConcept | None = None
    denominatorCount: FHIRInteger | None = None
    numeratorCount: FHIRInteger | None = None
    precisionEstimate: Annotated[list[RiskEvidenceSynthesisRiskEstimatePrecisionEstimate], Field(min_length=1)] | None = None
class RiskEvidenceSynthesisCertaintyCertaintySubcomponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    rating: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
class RiskEvidenceSynthesisCertainty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    rating: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    certaintySubcomponent: Annotated[list[RiskEvidenceSynthesisCertaintyCertaintySubcomponent], Field(min_length=1)] | None = None
class RiskEvidenceSynthesis(DomainResourceR4):
    resourceType: Literal['RiskEvidenceSynthesis']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    copyright: StrictStr | None = None
    approvalDate: FHIRDate | None = None
    lastReviewDate: FHIRDate | None = None
    effectivePeriod: fhir_types.Period | None = None
    topic: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    author: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    editor: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    reviewer: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    endorser: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    relatedArtifact: Annotated[list[fhir_types.RelatedArtifact], Field(min_length=1)] | None = None
    synthesisType: fhir_types.CodeableConcept | None = None
    studyType: fhir_types.CodeableConcept | None = None
    population: fhir_types.Reference
    exposure: fhir_types.Reference | None = None
    outcome: fhir_types.Reference
    sampleSize: RiskEvidenceSynthesisSampleSize | None = None
    riskEstimate: RiskEvidenceSynthesisRiskEstimate | None = None
    certainty: Annotated[list[RiskEvidenceSynthesisCertainty], Field(min_length=1)] | None = None

class Schedule(DomainResourceR4):
    resourceType: Literal['Schedule']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    active: StrictBool | None = None
    serviceCategory: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    serviceType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    actor: Annotated[list[fhir_types.Reference], Field(min_length=1)]
    planningHorizon: fhir_types.Period | None = None
    comment: StrictStr | None = None

class SearchParameterComponent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    definition: StrictStr
    expression: StrictStr
class SearchParameter(DomainResourceR4):
    resourceType: Literal['SearchParameter']
    url: StrictStr
    version: StrictStr | None = None
    name: StrictStr
    derivedFrom: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    code: FHIRCode
    base: Annotated[list[FHIRCode], Field(min_length=1)]
    type: Literal['composite', 'date', 'number', 'quantity', 'reference', 'special', 'string', 'token', 'uri']
    expression: StrictStr | None = None
    xpath: StrictStr | None = None
    xpathUsage: Literal['distance', 'nearby', 'normal', 'other', 'phonetic'] | None = None
    target: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    multipleOr: StrictBool | None = None
    multipleAnd: StrictBool | None = None
    comparator: Annotated[list[Literal['ap', 'eb', 'eq', 'ge', 'gt', 'le', 'lt', 'ne', 'sa']], Field(min_length=1)] | None = None
    modifier: Annotated[list[Literal['above', 'below', 'contains', 'exact', 'identifier', 'in', 'missing', 'not', 'not-in', 'ofType', 'text', 'type']], Field(min_length=1)] | None = None
    chain: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    component: Annotated[list[SearchParameterComponent], Field(min_length=1)] | None = None

class ServiceRequest(DomainResourceR4):
    resourceType: Literal['ServiceRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    instantiatesUri: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    replaces: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    requisition: fhir_types.Identifier | None = None
    status: Literal['active', 'completed', 'draft', 'entered-in-error', 'on-hold', 'revoked', 'unknown']
    intent: Literal['directive', 'filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order']
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    doNotPerform: StrictBool | None = None
    code: fhir_types.CodeableConcept | None = None
    orderDetail: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    quantityQuantity: fhir_types.Quantity | None = None
    quantityRatio: fhir_types.Ratio | None = None
    quantityRange: fhir_types.Range | None = None
    subject: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    asNeededBoolean: StrictBool | None = None
    asNeededCodeableConcept: fhir_types.CodeableConcept | None = None
    authoredOn: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    performerType: fhir_types.CodeableConcept | None = None
    performer: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    locationCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    locationReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    insurance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    supportingInfo: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    specimen: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    bodySite: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    patientInstruction: StrictStr | None = None
    relevantHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ServiceRequest':
        _present = sum(1 for _f in ('quantityQuantity', 'quantityRatio', 'quantityRange',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('quantity[x] allows at most one value')
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        _present = sum(1 for _f in ('asNeededBoolean', 'asNeededCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('asNeeded[x] allows at most one value')
        return self

class Slot(DomainResourceR4):
    resourceType: Literal['Slot']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    serviceCategory: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    serviceType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    specialty: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    appointmentType: fhir_types.CodeableConcept | None = None
    schedule: fhir_types.Reference
    status: Literal['busy', 'busy-tentative', 'busy-unavailable', 'entered-in-error', 'free']
    start: FHIRInstant
    end: FHIRInstant
    overbooked: StrictBool | None = None
    comment: StrictStr | None = None

class SpecimenCollection(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    collector: fhir_types.Reference | None = None
    collectedDateTime: FHIRDateTime | None = None
    collectedPeriod: fhir_types.Period | None = None
    duration: fhir_types.Duration | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    method: fhir_types.CodeableConcept | None = None
    bodySite: fhir_types.CodeableConcept | None = None
    fastingStatusCodeableConcept: fhir_types.CodeableConcept | None = None
    fastingStatusDuration: fhir_types.Duration | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SpecimenCollection':
        _present = sum(1 for _f in ('collectedDateTime', 'collectedPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('collected[x] allows at most one value')
        _present = sum(1 for _f in ('fastingStatusCodeableConcept', 'fastingStatusDuration',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('fastingStatus[x] allows at most one value')
        return self
class SpecimenProcessing(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    procedure: fhir_types.CodeableConcept | None = None
    additive: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    timeDateTime: FHIRDateTime | None = None
    timePeriod: fhir_types.Period | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SpecimenProcessing':
        _present = sum(1 for _f in ('timeDateTime', 'timePeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('time[x] allows at most one value')
        return self
class SpecimenContainer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    type: fhir_types.CodeableConcept | None = None
    capacity: fhir_types.SimpleQuantity | None = None
    specimenQuantity: fhir_types.SimpleQuantity | None = None
    additiveCodeableConcept: fhir_types.CodeableConcept | None = None
    additiveReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SpecimenContainer':
        _present = sum(1 for _f in ('additiveCodeableConcept', 'additiveReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('additive[x] allows at most one value')
        return self
class Specimen(DomainResourceR4):
    resourceType: Literal['Specimen']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    accessionIdentifier: fhir_types.Identifier | None = None
    status: Literal['available', 'entered-in-error', 'unavailable', 'unsatisfactory'] | None = None
    type: fhir_types.CodeableConcept | None = None
    subject: fhir_types.Reference | None = None
    receivedTime: FHIRDateTime | None = None
    parent: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    request: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    collection: SpecimenCollection | None = None
    processing: Annotated[list[SpecimenProcessing], Field(min_length=1)] | None = None
    container: Annotated[list[SpecimenContainer], Field(min_length=1)] | None = None
    condition: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None

class SpecimenDefinitionTypeTestedContainerAdditive(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    additiveCodeableConcept: fhir_types.CodeableConcept | None = None
    additiveReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SpecimenDefinitionTypeTestedContainerAdditive':
        _present = sum(1 for _f in ('additiveCodeableConcept', 'additiveReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('additive[x] requires exactly one value')
        return self
class SpecimenDefinitionTypeTestedContainer(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    material: fhir_types.CodeableConcept | None = None
    type: fhir_types.CodeableConcept | None = None
    cap: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    capacity: fhir_types.SimpleQuantity | None = None
    minimumVolumeQuantity: fhir_types.SimpleQuantity | None = None
    minimumVolumeString: StrictStr | None = None
    additive: Annotated[list[SpecimenDefinitionTypeTestedContainerAdditive], Field(min_length=1)] | None = None
    preparation: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SpecimenDefinitionTypeTestedContainer':
        _present = sum(1 for _f in ('minimumVolumeQuantity', 'minimumVolumeString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('minimumVolume[x] allows at most one value')
        return self
class SpecimenDefinitionTypeTestedHandling(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    temperatureQualifier: fhir_types.CodeableConcept | None = None
    temperatureRange: fhir_types.Range | None = None
    maxDuration: fhir_types.Duration | None = None
    instruction: StrictStr | None = None
class SpecimenDefinitionTypeTested(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    isDerived: StrictBool | None = None
    type: fhir_types.CodeableConcept | None = None
    preference: Literal['alternate', 'preferred']
    container: SpecimenDefinitionTypeTestedContainer | None = None
    requirement: StrictStr | None = None
    retentionTime: fhir_types.Duration | None = None
    rejectionCriterion: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    handling: Annotated[list[SpecimenDefinitionTypeTestedHandling], Field(min_length=1)] | None = None
class SpecimenDefinition(DomainResourceR4):
    resourceType: Literal['SpecimenDefinition']
    identifier: fhir_types.Identifier | None = None
    typeCollected: fhir_types.CodeableConcept | None = None
    patientPreparation: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    timeAspect: StrictStr | None = None
    collection: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    typeTested: Annotated[list[SpecimenDefinitionTypeTested], Field(min_length=1)] | None = None

class StructureDefinitionMapping(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identity: FHIRId
    uri: StrictStr | None = None
    name: StrictStr | None = None
    comment: StrictStr | None = None
class StructureDefinitionContext(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['element', 'extension', 'fhirpath']
    expression: StrictStr
class StructureDefinitionSnapshot(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    element: Annotated[list[fhir_types.ElementDefinition], Field(min_length=1)]
class StructureDefinitionDifferential(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    element: Annotated[list[fhir_types.ElementDefinition], Field(min_length=1)]
class StructureDefinition(DomainResourceR4):
    resourceType: Literal['StructureDefinition']
    url: StrictStr
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    keyword: Annotated[list[fhir_types.Coding], Field(min_length=1)] | None = None
    fhirVersion: Literal['0.0.80', '0.0.81', '0.0.82', '0.01', '0.05', '0.06', '0.11', '0.4.0', '0.5.0', '1.0.0', '1.0.1', '1.0.2', '1.1.0', '1.4.0', '1.6.0', '1.8.0', '3.0.0', '3.0.1', '3.3.0', '3.5.0', '4.0.0', '4.0.1'] | None = None
    mapping: Annotated[list[StructureDefinitionMapping], Field(min_length=1)] | None = None
    kind: Literal['complex-type', 'logical', 'primitive-type', 'resource']
    abstract: StrictBool
    context: Annotated[list[StructureDefinitionContext], Field(min_length=1)] | None = None
    contextInvariant: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    type: StrictStr
    baseDefinition: StrictStr | None = None
    derivation: Literal['constraint', 'specialization'] | None = None
    snapshot: StructureDefinitionSnapshot | None = None
    differential: StructureDefinitionDifferential | None = None

class StructureMapStructure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    url: StrictStr
    mode: Literal['produced', 'queried', 'source', 'target']
    alias: StrictStr | None = None
    documentation: StrictStr | None = None
class StructureMapGroupInput(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRId
    type: StrictStr | None = None
    mode: Literal['source', 'target']
    documentation: StrictStr | None = None
class StructureMapGroupRuleSource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    context: FHIRId
    min: FHIRInteger | None = None
    max: StrictStr | None = None
    type: StrictStr | None = None
    defaultValueBase64Binary: StrictStr | None = None
    defaultValueBoolean: StrictBool | None = None
    defaultValueCanonical: StrictStr | None = None
    defaultValueCode: FHIRCode | None = None
    defaultValueDate: FHIRDate | None = None
    defaultValueDateTime: FHIRDateTime | None = None
    defaultValueDecimal: FHIRDecimal | None = None
    defaultValueId: FHIRId | None = None
    defaultValueInstant: FHIRInstant | None = None
    defaultValueInteger: FHIRInteger | None = None
    defaultValueMarkdown: StrictStr | None = None
    defaultValueOid: StrictStr | None = None
    defaultValuePositiveInt: FHIRPositiveInt | None = None
    defaultValueString: StrictStr | None = None
    defaultValueTime: FHIRTime | None = None
    defaultValueUnsignedInt: FHIRUnsignedInt | None = None
    defaultValueUri: StrictStr | None = None
    defaultValueUrl: StrictStr | None = None
    defaultValueUuid: StrictStr | None = None
    defaultValueAddress: fhir_types.Address | None = None
    defaultValueAge: fhir_types.Age | None = None
    defaultValueAnnotation: fhir_types.Annotation | None = None
    defaultValueAttachment: fhir_types.Attachment | None = None
    defaultValueCodeableConcept: fhir_types.CodeableConcept | None = None
    defaultValueCoding: fhir_types.Coding | None = None
    defaultValueContactPoint: fhir_types.ContactPoint | None = None
    defaultValueCount: fhir_types.Count | None = None
    defaultValueDistance: fhir_types.Distance | None = None
    defaultValueDuration: fhir_types.Duration | None = None
    defaultValueHumanName: fhir_types.HumanName | None = None
    defaultValueIdentifier: fhir_types.Identifier | None = None
    defaultValueMoney: fhir_types.Money | None = None
    defaultValuePeriod: fhir_types.Period | None = None
    defaultValueQuantity: fhir_types.Quantity | None = None
    defaultValueRange: fhir_types.Range | None = None
    defaultValueRatio: fhir_types.Ratio | None = None
    defaultValueReference: fhir_types.Reference | None = None
    defaultValueSampledData: fhir_types.SampledData | None = None
    defaultValueSignature: fhir_types.Signature | None = None
    defaultValueTiming: fhir_types.Timing | None = None
    defaultValueContactDetail: fhir_types.ContactDetail | None = None
    defaultValueContributor: fhir_types.Contributor | None = None
    defaultValueDataRequirement: fhir_types.DataRequirement | None = None
    defaultValueExpression: fhir_types.Expression | None = None
    defaultValueParameterDefinition: fhir_types.ParameterDefinition | None = None
    defaultValueRelatedArtifact: fhir_types.RelatedArtifact | None = None
    defaultValueTriggerDefinition: fhir_types.TriggerDefinition | None = None
    defaultValueUsageContext: fhir_types.UsageContext | None = None
    defaultValueDosage: fhir_types.Dosage | None = None
    defaultValueMeta: fhir_types.Meta | None = None
    element: StrictStr | None = None
    listMode: Literal['first', 'last', 'not_first', 'not_last', 'only_one'] | None = None
    variable: FHIRId | None = None
    condition: StrictStr | None = None
    check: StrictStr | None = None
    logMessage: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'StructureMapGroupRuleSource':
        _present = sum(1 for _f in ('defaultValueBase64Binary', 'defaultValueBoolean', 'defaultValueCanonical', 'defaultValueCode', 'defaultValueDate', 'defaultValueDateTime', 'defaultValueDecimal', 'defaultValueId', 'defaultValueInstant', 'defaultValueInteger', 'defaultValueMarkdown', 'defaultValueOid', 'defaultValuePositiveInt', 'defaultValueString', 'defaultValueTime', 'defaultValueUnsignedInt', 'defaultValueUri', 'defaultValueUrl', 'defaultValueUuid', 'defaultValueAddress', 'defaultValueAge', 'defaultValueAnnotation', 'defaultValueAttachment', 'defaultValueCodeableConcept', 'defaultValueCoding', 'defaultValueContactPoint', 'defaultValueCount', 'defaultValueDistance', 'defaultValueDuration', 'defaultValueHumanName', 'defaultValueIdentifier', 'defaultValueMoney', 'defaultValuePeriod', 'defaultValueQuantity', 'defaultValueRange', 'defaultValueRatio', 'defaultValueReference', 'defaultValueSampledData', 'defaultValueSignature', 'defaultValueTiming', 'defaultValueContactDetail', 'defaultValueContributor', 'defaultValueDataRequirement', 'defaultValueExpression', 'defaultValueParameterDefinition', 'defaultValueRelatedArtifact', 'defaultValueTriggerDefinition', 'defaultValueUsageContext', 'defaultValueDosage', 'defaultValueMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('defaultValue[x] allows at most one value')
        return self
class StructureMapGroupRuleTargetParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    valueId: FHIRId | None = None
    valueString: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: FHIRInteger | None = None
    valueDecimal: FHIRDecimal | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'StructureMapGroupRuleTargetParameter':
        _present = sum(1 for _f in ('valueId', 'valueString', 'valueBoolean', 'valueInteger', 'valueDecimal',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class StructureMapGroupRuleTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    context: FHIRId | None = None
    contextType: Literal['type', 'variable'] | None = None
    element: StrictStr | None = None
    variable: FHIRId | None = None
    listMode: Annotated[list[Literal['collate', 'first', 'last', 'share']], Field(min_length=1)] | None = None
    listRuleId: FHIRId | None = None
    transform: Literal['append', 'c', 'cast', 'cc', 'copy', 'cp', 'create', 'dateOp', 'escape', 'evaluate', 'id', 'pointer', 'qty', 'reference', 'translate', 'truncate', 'uuid'] | None = None
    parameter: Annotated[list[StructureMapGroupRuleTargetParameter], Field(min_length=1)] | None = None
class StructureMapGroupRuleDependent(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRId
    variable: Annotated[list[StrictStr], Field(min_length=1)]
class StructureMapGroupRule(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRId
    source: Annotated[list[StructureMapGroupRuleSource], Field(min_length=1)]
    target: Annotated[list[StructureMapGroupRuleTarget], Field(min_length=1)] | None = None
    rule: Annotated[list[StructureMapGroupRule], Field(min_length=1)] | None = None
    dependent: Annotated[list[StructureMapGroupRuleDependent], Field(min_length=1)] | None = None
    documentation: StrictStr | None = None
class StructureMapGroup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRId
    extends: FHIRId | None = None
    typeMode: Literal['none', 'type-and-types', 'types']
    documentation: StrictStr | None = None
    input: Annotated[list[StructureMapGroupInput], Field(min_length=1)]
    rule: Annotated[list[StructureMapGroupRule], Field(min_length=1)]
class StructureMap(DomainResourceR4):
    resourceType: Literal['StructureMap']
    url: StrictStr
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    structure: Annotated[list[StructureMapStructure], Field(min_length=1)] | None = None
    import_: Annotated[list[StrictStr], Field(min_length=1)] | None = Field(default=None, alias='import')
    group: Annotated[list[StructureMapGroup], Field(min_length=1)]

class SubscriptionChannel(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['email', 'message', 'rest-hook', 'sms', 'websocket']
    endpoint: StrictStr | None = None
    payload: FHIRCode | None = None
    header: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class Subscription(DomainResourceR4):
    resourceType: Literal['Subscription']
    status: Literal['active', 'error', 'off', 'requested']
    contact: Annotated[list[fhir_types.ContactPoint], Field(min_length=1)] | None = None
    end: FHIRInstant | None = None
    reason: StrictStr
    criteria: StrictStr
    error: StrictStr | None = None
    channel: SubscriptionChannel

class SubstanceInstance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    expiry: FHIRDateTime | None = None
    quantity: fhir_types.SimpleQuantity | None = None
class SubstanceIngredient(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    quantity: fhir_types.Ratio | None = None
    substanceCodeableConcept: fhir_types.CodeableConcept | None = None
    substanceReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceIngredient':
        _present = sum(1 for _f in ('substanceCodeableConcept', 'substanceReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('substance[x] requires exactly one value')
        return self
class Substance(DomainResourceR4):
    resourceType: Literal['Substance']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'entered-in-error', 'inactive'] | None = None
    category: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept
    description: StrictStr | None = None
    instance: Annotated[list[SubstanceInstance], Field(min_length=1)] | None = None
    ingredient: Annotated[list[SubstanceIngredient], Field(min_length=1)] | None = None

class SubstanceNucleicAcidSubunitLinkage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    connectivity: StrictStr | None = None
    identifier: fhir_types.Identifier | None = None
    name: StrictStr | None = None
    residueSite: StrictStr | None = None
class SubstanceNucleicAcidSubunitSugar(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    name: StrictStr | None = None
    residueSite: StrictStr | None = None
class SubstanceNucleicAcidSubunit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    subunit: FHIRInteger | None = None
    sequence: StrictStr | None = None
    length: FHIRInteger | None = None
    sequenceAttachment: fhir_types.Attachment | None = None
    fivePrime: fhir_types.CodeableConcept | None = None
    threePrime: fhir_types.CodeableConcept | None = None
    linkage: Annotated[list[SubstanceNucleicAcidSubunitLinkage], Field(min_length=1)] | None = None
    sugar: Annotated[list[SubstanceNucleicAcidSubunitSugar], Field(min_length=1)] | None = None
class SubstanceNucleicAcid(DomainResourceR4):
    resourceType: Literal['SubstanceNucleicAcid']
    sequenceType: fhir_types.CodeableConcept | None = None
    numberOfSubunits: FHIRInteger | None = None
    areaOfHybridisation: StrictStr | None = None
    oligoNucleotideType: fhir_types.CodeableConcept | None = None
    subunit: Annotated[list[SubstanceNucleicAcidSubunit], Field(min_length=1)] | None = None

class SubstancePolymerMonomerSetStartingMaterial(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    material: fhir_types.CodeableConcept | None = None
    type: fhir_types.CodeableConcept | None = None
    isDefining: StrictBool | None = None
    amount: fhir_types.SubstanceAmount | None = None
class SubstancePolymerMonomerSet(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    ratioType: fhir_types.CodeableConcept | None = None
    startingMaterial: Annotated[list[SubstancePolymerMonomerSetStartingMaterial], Field(min_length=1)] | None = None
class SubstancePolymerRepeatRepeatUnitDegreeOfPolymerisation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    degree: fhir_types.CodeableConcept | None = None
    amount: fhir_types.SubstanceAmount | None = None
class SubstancePolymerRepeatRepeatUnitStructuralRepresentation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    representation: StrictStr | None = None
    attachment: fhir_types.Attachment | None = None
class SubstancePolymerRepeatRepeatUnit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    orientationOfPolymerisation: fhir_types.CodeableConcept | None = None
    repeatUnit: StrictStr | None = None
    amount: fhir_types.SubstanceAmount | None = None
    degreeOfPolymerisation: Annotated[list[SubstancePolymerRepeatRepeatUnitDegreeOfPolymerisation], Field(min_length=1)] | None = None
    structuralRepresentation: Annotated[list[SubstancePolymerRepeatRepeatUnitStructuralRepresentation], Field(min_length=1)] | None = None
class SubstancePolymerRepeat(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    numberOfUnits: FHIRInteger | None = None
    averageMolecularFormula: StrictStr | None = None
    repeatUnitAmountType: fhir_types.CodeableConcept | None = None
    repeatUnit: Annotated[list[SubstancePolymerRepeatRepeatUnit], Field(min_length=1)] | None = None
class SubstancePolymer(DomainResourceR4):
    resourceType: Literal['SubstancePolymer']
    class_: fhir_types.CodeableConcept | None = Field(default=None, alias='class')
    geometry: fhir_types.CodeableConcept | None = None
    copolymerConnectivity: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    modification: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    monomerSet: Annotated[list[SubstancePolymerMonomerSet], Field(min_length=1)] | None = None
    repeat: Annotated[list[SubstancePolymerRepeat], Field(min_length=1)] | None = None

class SubstanceProteinSubunit(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    subunit: FHIRInteger | None = None
    sequence: StrictStr | None = None
    length: FHIRInteger | None = None
    sequenceAttachment: fhir_types.Attachment | None = None
    nTerminalModificationId: fhir_types.Identifier | None = None
    nTerminalModification: StrictStr | None = None
    cTerminalModificationId: fhir_types.Identifier | None = None
    cTerminalModification: StrictStr | None = None
class SubstanceProtein(DomainResourceR4):
    resourceType: Literal['SubstanceProtein']
    sequenceType: fhir_types.CodeableConcept | None = None
    numberOfSubunits: FHIRInteger | None = None
    disulfideLinkage: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    subunit: Annotated[list[SubstanceProteinSubunit], Field(min_length=1)] | None = None

class SubstanceReferenceInformationGene(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    geneSequenceOrigin: fhir_types.CodeableConcept | None = None
    gene: fhir_types.CodeableConcept | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class SubstanceReferenceInformationGeneElement(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    element: fhir_types.Identifier | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class SubstanceReferenceInformationClassification(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    domain: fhir_types.CodeableConcept | None = None
    classification: fhir_types.CodeableConcept | None = None
    subtype: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class SubstanceReferenceInformationTarget(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    target: fhir_types.Identifier | None = None
    type: fhir_types.CodeableConcept | None = None
    interaction: fhir_types.CodeableConcept | None = None
    organism: fhir_types.CodeableConcept | None = None
    organismType: fhir_types.CodeableConcept | None = None
    amountQuantity: fhir_types.Quantity | None = None
    amountRange: fhir_types.Range | None = None
    amountString: StrictStr | None = None
    amountType: fhir_types.CodeableConcept | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceReferenceInformationTarget':
        _present = sum(1 for _f in ('amountQuantity', 'amountRange', 'amountString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('amount[x] allows at most one value')
        return self
class SubstanceReferenceInformation(DomainResourceR4):
    resourceType: Literal['SubstanceReferenceInformation']
    comment: StrictStr | None = None
    gene: Annotated[list[SubstanceReferenceInformationGene], Field(min_length=1)] | None = None
    geneElement: Annotated[list[SubstanceReferenceInformationGeneElement], Field(min_length=1)] | None = None
    classification: Annotated[list[SubstanceReferenceInformationClassification], Field(min_length=1)] | None = None
    target: Annotated[list[SubstanceReferenceInformationTarget], Field(min_length=1)] | None = None

class SubstanceSourceMaterialFractionDescription(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    fraction: StrictStr | None = None
    materialType: fhir_types.CodeableConcept | None = None
class SubstanceSourceMaterialOrganismAuthor(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    authorType: fhir_types.CodeableConcept | None = None
    authorDescription: StrictStr | None = None
class SubstanceSourceMaterialOrganismHybrid(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    maternalOrganismId: StrictStr | None = None
    maternalOrganismName: StrictStr | None = None
    paternalOrganismId: StrictStr | None = None
    paternalOrganismName: StrictStr | None = None
    hybridType: fhir_types.CodeableConcept | None = None
class SubstanceSourceMaterialOrganismOrganismGeneral(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    kingdom: fhir_types.CodeableConcept | None = None
    phylum: fhir_types.CodeableConcept | None = None
    class_: fhir_types.CodeableConcept | None = Field(default=None, alias='class')
    order: fhir_types.CodeableConcept | None = None
class SubstanceSourceMaterialOrganism(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    family: fhir_types.CodeableConcept | None = None
    genus: fhir_types.CodeableConcept | None = None
    species: fhir_types.CodeableConcept | None = None
    intraspecificType: fhir_types.CodeableConcept | None = None
    intraspecificDescription: StrictStr | None = None
    author: Annotated[list[SubstanceSourceMaterialOrganismAuthor], Field(min_length=1)] | None = None
    hybrid: SubstanceSourceMaterialOrganismHybrid | None = None
    organismGeneral: SubstanceSourceMaterialOrganismOrganismGeneral | None = None
class SubstanceSourceMaterialPartDescription(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    part: fhir_types.CodeableConcept | None = None
    partLocation: fhir_types.CodeableConcept | None = None
class SubstanceSourceMaterial(DomainResourceR4):
    resourceType: Literal['SubstanceSourceMaterial']
    sourceMaterialClass: fhir_types.CodeableConcept | None = None
    sourceMaterialType: fhir_types.CodeableConcept | None = None
    sourceMaterialState: fhir_types.CodeableConcept | None = None
    organismId: fhir_types.Identifier | None = None
    organismName: StrictStr | None = None
    parentSubstanceId: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    parentSubstanceName: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    countryOfOrigin: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    geographicalLocation: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    developmentStage: fhir_types.CodeableConcept | None = None
    fractionDescription: Annotated[list[SubstanceSourceMaterialFractionDescription], Field(min_length=1)] | None = None
    organism: SubstanceSourceMaterialOrganism | None = None
    partDescription: Annotated[list[SubstanceSourceMaterialPartDescription], Field(min_length=1)] | None = None

class SubstanceSpecificationMoiety(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    role: fhir_types.CodeableConcept | None = None
    identifier: fhir_types.Identifier | None = None
    name: StrictStr | None = None
    stereochemistry: fhir_types.CodeableConcept | None = None
    opticalActivity: fhir_types.CodeableConcept | None = None
    molecularFormula: StrictStr | None = None
    amountQuantity: fhir_types.Quantity | None = None
    amountString: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceSpecificationMoiety':
        _present = sum(1 for _f in ('amountQuantity', 'amountString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('amount[x] allows at most one value')
        return self
class SubstanceSpecificationProperty(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    category: fhir_types.CodeableConcept | None = None
    code: fhir_types.CodeableConcept | None = None
    parameters: StrictStr | None = None
    definingSubstanceReference: fhir_types.Reference | None = None
    definingSubstanceCodeableConcept: fhir_types.CodeableConcept | None = None
    amountQuantity: fhir_types.Quantity | None = None
    amountString: StrictStr | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceSpecificationProperty':
        _present = sum(1 for _f in ('definingSubstanceReference', 'definingSubstanceCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('definingSubstance[x] allows at most one value')
        _present = sum(1 for _f in ('amountQuantity', 'amountString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('amount[x] allows at most one value')
        return self
class SubstanceSpecificationStructureIsotopeMolecularWeight(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    method: fhir_types.CodeableConcept | None = None
    type: fhir_types.CodeableConcept | None = None
    amount: fhir_types.Quantity | None = None
class SubstanceSpecificationStructureIsotope(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: fhir_types.Identifier | None = None
    name: fhir_types.CodeableConcept | None = None
    substitution: fhir_types.CodeableConcept | None = None
    halfLife: fhir_types.Quantity | None = None
    molecularWeight: SubstanceSpecificationStructureIsotopeMolecularWeight | None = None
class SubstanceSpecificationStructureRepresentation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept | None = None
    representation: StrictStr | None = None
    attachment: fhir_types.Attachment | None = None
class SubstanceSpecificationStructure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    stereochemistry: fhir_types.CodeableConcept | None = None
    opticalActivity: fhir_types.CodeableConcept | None = None
    molecularFormula: StrictStr | None = None
    molecularFormulaByMoiety: StrictStr | None = None
    isotope: Annotated[list[SubstanceSpecificationStructureIsotope], Field(min_length=1)] | None = None
    molecularWeight: SubstanceSpecificationStructureIsotopeMolecularWeight | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    representation: Annotated[list[SubstanceSpecificationStructureRepresentation], Field(min_length=1)] | None = None
class SubstanceSpecificationCode(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    status: fhir_types.CodeableConcept | None = None
    statusDate: FHIRDateTime | None = None
    comment: StrictStr | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class SubstanceSpecificationNameOfficial(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    authority: fhir_types.CodeableConcept | None = None
    status: fhir_types.CodeableConcept | None = None
    date: FHIRDateTime | None = None
class SubstanceSpecificationName(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    type: fhir_types.CodeableConcept | None = None
    status: fhir_types.CodeableConcept | None = None
    preferred: StrictBool | None = None
    language: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    domain: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    synonym: Annotated[list[SubstanceSpecificationName], Field(min_length=1)] | None = None
    translation: Annotated[list[SubstanceSpecificationName], Field(min_length=1)] | None = None
    official: Annotated[list[SubstanceSpecificationNameOfficial], Field(min_length=1)] | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class SubstanceSpecificationRelationship(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    substanceReference: fhir_types.Reference | None = None
    substanceCodeableConcept: fhir_types.CodeableConcept | None = None
    relationship: fhir_types.CodeableConcept | None = None
    isDefining: StrictBool | None = None
    amountQuantity: fhir_types.Quantity | None = None
    amountRange: fhir_types.Range | None = None
    amountRatio: fhir_types.Ratio | None = None
    amountString: StrictStr | None = None
    amountRatioLowLimit: fhir_types.Ratio | None = None
    amountType: fhir_types.CodeableConcept | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceSpecificationRelationship':
        _present = sum(1 for _f in ('substanceReference', 'substanceCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('substance[x] allows at most one value')
        _present = sum(1 for _f in ('amountQuantity', 'amountRange', 'amountRatio', 'amountString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('amount[x] allows at most one value')
        return self
class SubstanceSpecification(DomainResourceR4):
    resourceType: Literal['SubstanceSpecification']
    identifier: fhir_types.Identifier | None = None
    type: fhir_types.CodeableConcept | None = None
    status: fhir_types.CodeableConcept | None = None
    domain: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    source: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    comment: StrictStr | None = None
    moiety: Annotated[list[SubstanceSpecificationMoiety], Field(min_length=1)] | None = None
    property: Annotated[list[SubstanceSpecificationProperty], Field(min_length=1)] | None = None
    referenceInformation: fhir_types.Reference | None = None
    structure: SubstanceSpecificationStructure | None = None
    code: Annotated[list[SubstanceSpecificationCode], Field(min_length=1)] | None = None
    name: Annotated[list[SubstanceSpecificationName], Field(min_length=1)] | None = None
    molecularWeight: Annotated[list[SubstanceSpecificationStructureIsotopeMolecularWeight], Field(min_length=1)] | None = None
    relationship: Annotated[list[SubstanceSpecificationRelationship], Field(min_length=1)] | None = None
    nucleicAcid: fhir_types.Reference | None = None
    polymer: fhir_types.Reference | None = None
    protein: fhir_types.Reference | None = None
    sourceMaterial: fhir_types.Reference | None = None

class SupplyDeliverySuppliedItem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    quantity: fhir_types.SimpleQuantity | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None
    itemReference: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SupplyDeliverySuppliedItem':
        _present = sum(1 for _f in ('itemCodeableConcept', 'itemReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('item[x] allows at most one value')
        return self
class SupplyDelivery(DomainResourceR4):
    resourceType: Literal['SupplyDelivery']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['abandoned', 'completed', 'entered-in-error', 'in-progress'] | None = None
    patient: fhir_types.Reference | None = None
    type: fhir_types.CodeableConcept | None = None
    suppliedItem: SupplyDeliverySuppliedItem | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    supplier: fhir_types.Reference | None = None
    destination: fhir_types.Reference | None = None
    receiver: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SupplyDelivery':
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self

class SupplyRequestParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: fhir_types.CodeableConcept | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueBoolean: StrictBool | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SupplyRequestParameter':
        _present = sum(1 for _f in ('valueCodeableConcept', 'valueQuantity', 'valueRange', 'valueBoolean',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class SupplyRequest(DomainResourceR4):
    resourceType: Literal['SupplyRequest']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'completed', 'draft', 'entered-in-error', 'suspended', 'unknown'] | None = None
    category: fhir_types.CodeableConcept | None = None
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    itemCodeableConcept: fhir_types.CodeableConcept | None = None
    itemReference: fhir_types.Reference | None = None
    quantity: fhir_types.Quantity
    parameter: Annotated[list[SupplyRequestParameter], Field(min_length=1)] | None = None
    occurrenceDateTime: FHIRDateTime | None = None
    occurrencePeriod: fhir_types.Period | None = None
    occurrenceTiming: fhir_types.Timing | None = None
    authoredOn: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    supplier: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    reasonCode: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    reasonReference: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    deliverFrom: fhir_types.Reference | None = None
    deliverTo: fhir_types.Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SupplyRequest':
        _present = sum(1 for _f in ('itemCodeableConcept', 'itemReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('item[x] requires exactly one value')
        _present = sum(1 for _f in ('occurrenceDateTime', 'occurrencePeriod', 'occurrenceTiming',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('occurrence[x] allows at most one value')
        return self

class TaskRestriction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    repetitions: FHIRPositiveInt | None = None
    period: fhir_types.Period | None = None
    recipient: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
class TaskInput(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    valueBase64Binary: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueCanonical: StrictStr | None = None
    valueCode: FHIRCode | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueDecimal: FHIRDecimal | None = None
    valueId: FHIRId | None = None
    valueInstant: FHIRInstant | None = None
    valueInteger: FHIRInteger | None = None
    valueMarkdown: StrictStr | None = None
    valueOid: StrictStr | None = None
    valuePositiveInt: FHIRPositiveInt | None = None
    valueString: StrictStr | None = None
    valueTime: FHIRTime | None = None
    valueUnsignedInt: FHIRUnsignedInt | None = None
    valueUri: StrictStr | None = None
    valueUrl: StrictStr | None = None
    valueUuid: StrictStr | None = None
    valueAddress: fhir_types.Address | None = None
    valueAge: fhir_types.Age | None = None
    valueAnnotation: fhir_types.Annotation | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueCoding: fhir_types.Coding | None = None
    valueContactPoint: fhir_types.ContactPoint | None = None
    valueCount: fhir_types.Count | None = None
    valueDistance: fhir_types.Distance | None = None
    valueDuration: fhir_types.Duration | None = None
    valueHumanName: fhir_types.HumanName | None = None
    valueIdentifier: fhir_types.Identifier | None = None
    valueMoney: fhir_types.Money | None = None
    valuePeriod: fhir_types.Period | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueRatio: fhir_types.Ratio | None = None
    valueReference: fhir_types.Reference | None = None
    valueSampledData: fhir_types.SampledData | None = None
    valueSignature: fhir_types.Signature | None = None
    valueTiming: fhir_types.Timing | None = None
    valueContactDetail: fhir_types.ContactDetail | None = None
    valueContributor: fhir_types.Contributor | None = None
    valueDataRequirement: fhir_types.DataRequirement | None = None
    valueExpression: fhir_types.Expression | None = None
    valueParameterDefinition: fhir_types.ParameterDefinition | None = None
    valueRelatedArtifact: fhir_types.RelatedArtifact | None = None
    valueTriggerDefinition: fhir_types.TriggerDefinition | None = None
    valueUsageContext: fhir_types.UsageContext | None = None
    valueDosage: fhir_types.Dosage | None = None
    valueMeta: fhir_types.Meta | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'TaskInput':
        _present = sum(1 for _f in ('valueBase64Binary', 'valueBoolean', 'valueCanonical', 'valueCode', 'valueDate', 'valueDateTime', 'valueDecimal', 'valueId', 'valueInstant', 'valueInteger', 'valueMarkdown', 'valueOid', 'valuePositiveInt', 'valueString', 'valueTime', 'valueUnsignedInt', 'valueUri', 'valueUrl', 'valueUuid', 'valueAddress', 'valueAge', 'valueAnnotation', 'valueAttachment', 'valueCodeableConcept', 'valueCoding', 'valueContactPoint', 'valueCount', 'valueDistance', 'valueDuration', 'valueHumanName', 'valueIdentifier', 'valueMoney', 'valuePeriod', 'valueQuantity', 'valueRange', 'valueRatio', 'valueReference', 'valueSampledData', 'valueSignature', 'valueTiming', 'valueContactDetail', 'valueContributor', 'valueDataRequirement', 'valueExpression', 'valueParameterDefinition', 'valueRelatedArtifact', 'valueTriggerDefinition', 'valueUsageContext', 'valueDosage', 'valueMeta',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class TaskOutput(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.CodeableConcept
    valueBase64Binary: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueCanonical: StrictStr | None = None
    valueCode: FHIRCode | None = None
    valueDate: FHIRDate | None = None
    valueDateTime: FHIRDateTime | None = None
    valueDecimal: FHIRDecimal | None = None
    valueId: FHIRId | None = None
    valueInstant: FHIRInstant | None = None
    valueInteger: FHIRInteger | None = None
    valueMarkdown: StrictStr | None = None
    valueOid: StrictStr | None = None
    valuePositiveInt: FHIRPositiveInt | None = None
    valueString: StrictStr | None = None
    valueTime: FHIRTime | None = None
    valueUnsignedInt: FHIRUnsignedInt | None = None
    valueUri: StrictStr | None = None
    valueUrl: StrictStr | None = None
    valueUuid: StrictStr | None = None
    valueAddress: fhir_types.Address | None = None
    valueAge: fhir_types.Age | None = None
    valueAnnotation: fhir_types.Annotation | None = None
    valueAttachment: fhir_types.Attachment | None = None
    valueCodeableConcept: fhir_types.CodeableConcept | None = None
    valueCoding: fhir_types.Coding | None = None
    valueContactPoint: fhir_types.ContactPoint | None = None
    valueCount: fhir_types.Count | None = None
    valueDistance: fhir_types.Distance | None = None
    valueDuration: fhir_types.Duration | None = None
    valueHumanName: fhir_types.HumanName | None = None
    valueIdentifier: fhir_types.Identifier | None = None
    valueMoney: fhir_types.Money | None = None
    valuePeriod: fhir_types.Period | None = None
    valueQuantity: fhir_types.Quantity | None = None
    valueRange: fhir_types.Range | None = None
    valueRatio: fhir_types.Ratio | None = None
    valueReference: fhir_types.Reference | None = None
    valueSampledData: fhir_types.SampledData | None = None
    valueSignature: fhir_types.Signature | None = None
    valueTiming: fhir_types.Timing | None = None
    valueContactDetail: fhir_types.ContactDetail | None = None
    valueContributor: fhir_types.Contributor | None = None
    valueDataRequirement: fhir_types.DataRequirement | None = None
    valueExpression: fhir_types.Expression | None = None
    valueParameterDefinition: fhir_types.ParameterDefinition | None = None
    valueRelatedArtifact: fhir_types.RelatedArtifact | None = None
    valueTriggerDefinition: fhir_types.TriggerDefinition | None = None
    valueUsageContext: fhir_types.UsageContext | None = None
    valueDosage: fhir_types.Dosage | None = None
    valueMeta: fhir_types.Meta | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'TaskOutput':
        _present = sum(1 for _f in ('valueBase64Binary', 'valueBoolean', 'valueCanonical', 'valueCode', 'valueDate', 'valueDateTime', 'valueDecimal', 'valueId', 'valueInstant', 'valueInteger', 'valueMarkdown', 'valueOid', 'valuePositiveInt', 'valueString', 'valueTime', 'valueUnsignedInt', 'valueUri', 'valueUrl', 'valueUuid', 'valueAddress', 'valueAge', 'valueAnnotation', 'valueAttachment', 'valueCodeableConcept', 'valueCoding', 'valueContactPoint', 'valueCount', 'valueDistance', 'valueDuration', 'valueHumanName', 'valueIdentifier', 'valueMoney', 'valuePeriod', 'valueQuantity', 'valueRange', 'valueRatio', 'valueReference', 'valueSampledData', 'valueSignature', 'valueTiming', 'valueContactDetail', 'valueContributor', 'valueDataRequirement', 'valueExpression', 'valueParameterDefinition', 'valueRelatedArtifact', 'valueTriggerDefinition', 'valueUsageContext', 'valueDosage', 'valueMeta',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class Task(DomainResourceR4):
    resourceType: Literal['Task']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    instantiatesCanonical: StrictStr | None = None
    instantiatesUri: StrictStr | None = None
    basedOn: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    groupIdentifier: fhir_types.Identifier | None = None
    partOf: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    status: Literal['accepted', 'cancelled', 'completed', 'draft', 'entered-in-error', 'failed', 'in-progress', 'on-hold', 'ready', 'received', 'rejected', 'requested']
    statusReason: fhir_types.CodeableConcept | None = None
    businessStatus: fhir_types.CodeableConcept | None = None
    intent: Literal['filler-order', 'instance-order', 'option', 'order', 'original-order', 'plan', 'proposal', 'reflex-order', 'unknown']
    priority: Literal['asap', 'routine', 'stat', 'urgent'] | None = None
    code: fhir_types.CodeableConcept | None = None
    description: StrictStr | None = None
    focus: fhir_types.Reference | None = None
    for_: fhir_types.Reference | None = Field(default=None, alias='for')
    encounter: fhir_types.Reference | None = None
    executionPeriod: fhir_types.Period | None = None
    authoredOn: FHIRDateTime | None = None
    lastModified: FHIRDateTime | None = None
    requester: fhir_types.Reference | None = None
    performerType: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    owner: fhir_types.Reference | None = None
    location: fhir_types.Reference | None = None
    reasonCode: fhir_types.CodeableConcept | None = None
    reasonReference: fhir_types.Reference | None = None
    insurance: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
    relevantHistory: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    restriction: TaskRestriction | None = None
    input: Annotated[list[TaskInput], Field(min_length=1)] | None = None
    output: Annotated[list[TaskOutput], Field(min_length=1)] | None = None

class TerminologyCapabilitiesSoftware(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    version: StrictStr | None = None
class TerminologyCapabilitiesImplementation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    description: StrictStr
    url: StrictStr | None = None
class TerminologyCapabilitiesCodeSystemVersionFilter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    op: Annotated[list[FHIRCode], Field(min_length=1)]
class TerminologyCapabilitiesCodeSystemVersion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: StrictStr | None = None
    isDefault: StrictBool | None = None
    compositional: StrictBool | None = None
    language: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
    filter: Annotated[list[TerminologyCapabilitiesCodeSystemVersionFilter], Field(min_length=1)] | None = None
    property: Annotated[list[FHIRCode], Field(min_length=1)] | None = None
class TerminologyCapabilitiesCodeSystem(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    uri: StrictStr | None = None
    version: Annotated[list[TerminologyCapabilitiesCodeSystemVersion], Field(min_length=1)] | None = None
    subsumption: StrictBool | None = None
class TerminologyCapabilitiesExpansionParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: FHIRCode
    documentation: StrictStr | None = None
class TerminologyCapabilitiesExpansion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    hierarchical: StrictBool | None = None
    paging: StrictBool | None = None
    incomplete: StrictBool | None = None
    parameter: Annotated[list[TerminologyCapabilitiesExpansionParameter], Field(min_length=1)] | None = None
    textFilter: StrictStr | None = None
class TerminologyCapabilitiesValidateCode(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    translations: StrictBool
class TerminologyCapabilitiesTranslation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    needsMap: StrictBool
class TerminologyCapabilitiesClosure(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    translation: StrictBool | None = None
class TerminologyCapabilities(DomainResourceR4):
    resourceType: Literal['TerminologyCapabilities']
    url: StrictStr | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    kind: Literal['capability', 'instance', 'requirements']
    software: TerminologyCapabilitiesSoftware | None = None
    implementation: TerminologyCapabilitiesImplementation | None = None
    lockedDate: StrictBool | None = None
    codeSystem: Annotated[list[TerminologyCapabilitiesCodeSystem], Field(min_length=1)] | None = None
    expansion: TerminologyCapabilitiesExpansion | None = None
    codeSearch: Literal['all', 'explicit'] | None = None
    validateCode: TerminologyCapabilitiesValidateCode | None = None
    translation: TerminologyCapabilitiesTranslation | None = None
    closure: TerminologyCapabilitiesClosure | None = None

class TestReportParticipant(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: Literal['client', 'server', 'test-engine']
    uri: StrictStr
    display: StrictStr | None = None
class TestReportSetupActionOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    result: Literal['error', 'fail', 'pass', 'skip', 'warning']
    message: StrictStr | None = None
    detail: StrictStr | None = None
class TestReportSetupActionAssert(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    result: Literal['error', 'fail', 'pass', 'skip', 'warning']
    message: StrictStr | None = None
    detail: StrictStr | None = None
class TestReportSetupAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestReportSetupActionOperation | None = None
    assert_: TestReportSetupActionAssert | None = Field(default=None, alias='assert')
class TestReportSetup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: Annotated[list[TestReportSetupAction], Field(min_length=1)]
class TestReportTestAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestReportSetupActionOperation | None = None
    assert_: TestReportSetupActionAssert | None = Field(default=None, alias='assert')
class TestReportTest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    action: Annotated[list[TestReportTestAction], Field(min_length=1)]
class TestReportTeardownAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestReportSetupActionOperation
class TestReportTeardown(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: Annotated[list[TestReportTeardownAction], Field(min_length=1)]
class TestReport(DomainResourceR4):
    resourceType: Literal['TestReport']
    identifier: fhir_types.Identifier | None = None
    name: StrictStr | None = None
    status: Literal['completed', 'entered-in-error', 'in-progress', 'stopped', 'waiting']
    testScript: fhir_types.Reference
    result: Literal['fail', 'pass', 'pending']
    score: FHIRDecimal | None = None
    tester: StrictStr | None = None
    issued: FHIRDateTime | None = None
    participant: Annotated[list[TestReportParticipant], Field(min_length=1)] | None = None
    setup: TestReportSetup | None = None
    test: Annotated[list[TestReportTest], Field(min_length=1)] | None = None
    teardown: TestReportTeardown | None = None

class TestScriptOrigin(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    index: FHIRInteger
    profile: fhir_types.Coding
class TestScriptDestination(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    index: FHIRInteger
    profile: fhir_types.Coding
class TestScriptMetadataLink(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    url: StrictStr
    description: StrictStr | None = None
class TestScriptMetadataCapability(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    required: StrictBool
    validated: StrictBool
    description: StrictStr | None = None
    origin: Annotated[list[FHIRInteger], Field(min_length=1)] | None = None
    destination: FHIRInteger | None = None
    link: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    capabilities: StrictStr
class TestScriptMetadata(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    link: Annotated[list[TestScriptMetadataLink], Field(min_length=1)] | None = None
    capability: Annotated[list[TestScriptMetadataCapability], Field(min_length=1)]
class TestScriptFixture(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    autocreate: StrictBool
    autodelete: StrictBool
    resource: fhir_types.Reference | None = None
class TestScriptVariable(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    defaultValue: StrictStr | None = None
    description: StrictStr | None = None
    expression: StrictStr | None = None
    headerField: StrictStr | None = None
    hint: StrictStr | None = None
    path: StrictStr | None = None
    sourceId: FHIRId | None = None
class TestScriptSetupActionOperationRequestHeader(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    field: StrictStr
    value: StrictStr
class TestScriptSetupActionOperation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    type: fhir_types.Coding | None = None
    resource: FHIRCode | None = None
    label: StrictStr | None = None
    description: StrictStr | None = None
    accept: FHIRCode | None = None
    contentType: FHIRCode | None = None
    destination: FHIRInteger | None = None
    encodeRequestUrl: StrictBool
    method: Literal['delete', 'get', 'head', 'options', 'patch', 'post', 'put'] | None = None
    origin: FHIRInteger | None = None
    params: StrictStr | None = None
    requestHeader: Annotated[list[TestScriptSetupActionOperationRequestHeader], Field(min_length=1)] | None = None
    requestId: FHIRId | None = None
    responseId: FHIRId | None = None
    sourceId: FHIRId | None = None
    targetId: FHIRId | None = None
    url: StrictStr | None = None
class TestScriptSetupActionAssert(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    label: StrictStr | None = None
    description: StrictStr | None = None
    direction: Literal['request', 'response'] | None = None
    compareToSourceId: StrictStr | None = None
    compareToSourceExpression: StrictStr | None = None
    compareToSourcePath: StrictStr | None = None
    contentType: FHIRCode | None = None
    expression: StrictStr | None = None
    headerField: StrictStr | None = None
    minimumId: StrictStr | None = None
    navigationLinks: StrictBool | None = None
    operator: Literal['contains', 'empty', 'equals', 'eval', 'greaterThan', 'in', 'lessThan', 'notContains', 'notEmpty', 'notEquals', 'notIn'] | None = None
    path: StrictStr | None = None
    requestMethod: Literal['delete', 'get', 'head', 'options', 'patch', 'post', 'put'] | None = None
    requestURL: StrictStr | None = None
    resource: FHIRCode | None = None
    response: Literal['bad', 'conflict', 'created', 'forbidden', 'gone', 'methodNotAllowed', 'noContent', 'notFound', 'notModified', 'okay', 'preconditionFailed', 'unprocessable'] | None = None
    responseCode: StrictStr | None = None
    sourceId: FHIRId | None = None
    validateProfileId: FHIRId | None = None
    value: StrictStr | None = None
    warningOnly: StrictBool
class TestScriptSetupAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestScriptSetupActionOperation | None = None
    assert_: TestScriptSetupActionAssert | None = Field(default=None, alias='assert')
class TestScriptSetup(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: Annotated[list[TestScriptSetupAction], Field(min_length=1)]
class TestScriptTestAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestScriptSetupActionOperation | None = None
    assert_: TestScriptSetupActionAssert | None = Field(default=None, alias='assert')
class TestScriptTest(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    description: StrictStr | None = None
    action: Annotated[list[TestScriptTestAction], Field(min_length=1)]
class TestScriptTeardownAction(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    operation: TestScriptSetupActionOperation
class TestScriptTeardown(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    action: Annotated[list[TestScriptTeardownAction], Field(min_length=1)]
class TestScript(DomainResourceR4):
    resourceType: Literal['TestScript']
    url: StrictStr
    identifier: fhir_types.Identifier | None = None
    version: StrictStr | None = None
    name: StrictStr
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    origin: Annotated[list[TestScriptOrigin], Field(min_length=1)] | None = None
    destination: Annotated[list[TestScriptDestination], Field(min_length=1)] | None = None
    metadata: TestScriptMetadata | None = None
    fixture: Annotated[list[TestScriptFixture], Field(min_length=1)] | None = None
    profile: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    variable: Annotated[list[TestScriptVariable], Field(min_length=1)] | None = None
    setup: TestScriptSetup | None = None
    test: Annotated[list[TestScriptTest], Field(min_length=1)] | None = None
    teardown: TestScriptTeardown | None = None

class ValueSetComposeIncludeConceptDesignation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    language: FHIRCode | None = None
    use: fhir_types.Coding | None = None
    value: StrictStr
class ValueSetComposeIncludeConcept(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    code: FHIRCode
    display: StrictStr | None = None
    designation: Annotated[list[ValueSetComposeIncludeConceptDesignation], Field(min_length=1)] | None = None
class ValueSetComposeIncludeFilter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    property: FHIRCode
    op: Literal['=', 'descendent-of', 'exists', 'generalizes', 'in', 'is-a', 'is-not-a', 'not-in', 'regex']
    value: StrictStr
class ValueSetComposeInclude(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    system: StrictStr | None = None
    version: StrictStr | None = None
    concept: Annotated[list[ValueSetComposeIncludeConcept], Field(min_length=1)] | None = None
    filter: Annotated[list[ValueSetComposeIncludeFilter], Field(min_length=1)] | None = None
    valueSet: Annotated[list[StrictStr], Field(min_length=1)] | None = None
class ValueSetCompose(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    lockedDate: FHIRDate | None = None
    inactive: StrictBool | None = None
    include: Annotated[list[ValueSetComposeInclude], Field(min_length=1)]
    exclude: Annotated[list[ValueSetComposeInclude], Field(min_length=1)] | None = None
class ValueSetExpansionParameter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    name: StrictStr
    valueString: StrictStr | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: FHIRInteger | None = None
    valueDecimal: FHIRDecimal | None = None
    valueUri: StrictStr | None = None
    valueCode: FHIRCode | None = None
    valueDateTime: FHIRDateTime | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ValueSetExpansionParameter':
        _present = sum(1 for _f in ('valueString', 'valueBoolean', 'valueInteger', 'valueDecimal', 'valueUri', 'valueCode', 'valueDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class ValueSetExpansionContains(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    system: StrictStr | None = None
    abstract: StrictBool | None = None
    inactive: StrictBool | None = None
    version: StrictStr | None = None
    code: FHIRCode | None = None
    display: StrictStr | None = None
    designation: Annotated[list[ValueSetComposeIncludeConceptDesignation], Field(min_length=1)] | None = None
    contains: Annotated[list[ValueSetExpansionContains], Field(min_length=1)] | None = None
class ValueSetExpansion(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    identifier: StrictStr | None = None
    timestamp: FHIRDateTime
    total: FHIRInteger | None = None
    offset: FHIRInteger | None = None
    parameter: Annotated[list[ValueSetExpansionParameter], Field(min_length=1)] | None = None
    contains: Annotated[list[ValueSetExpansionContains], Field(min_length=1)] | None = None
class ValueSet(DomainResourceR4):
    resourceType: Literal['ValueSet']
    url: StrictStr | None = None
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    version: StrictStr | None = None
    name: StrictStr | None = None
    title: StrictStr | None = None
    status: Literal['active', 'draft', 'retired', 'unknown']
    experimental: StrictBool | None = None
    date: FHIRDateTime | None = None
    publisher: StrictStr | None = None
    contact: Annotated[list[fhir_types.ContactDetail], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    useContext: Annotated[list[fhir_types.UsageContext], Field(min_length=1)] | None = None
    jurisdiction: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    immutable: StrictBool | None = None
    purpose: StrictStr | None = None
    copyright: StrictStr | None = None
    compose: ValueSetCompose | None = None
    expansion: ValueSetExpansion | None = None

class VerificationResultPrimarySource(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    who: fhir_types.Reference | None = None
    type: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    communicationMethod: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    validationStatus: fhir_types.CodeableConcept | None = None
    validationDate: FHIRDateTime | None = None
    canPushUpdates: fhir_types.CodeableConcept | None = None
    pushTypeAvailable: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
class VerificationResultAttestation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    who: fhir_types.Reference | None = None
    onBehalfOf: fhir_types.Reference | None = None
    communicationMethod: fhir_types.CodeableConcept | None = None
    date: FHIRDate | None = None
    sourceIdentityCertificate: StrictStr | None = None
    proxyIdentityCertificate: StrictStr | None = None
    proxySignature: fhir_types.Signature | None = None
    sourceSignature: fhir_types.Signature | None = None
class VerificationResultValidator(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    organization: fhir_types.Reference
    identityCertificate: StrictStr | None = None
    attestationSignature: fhir_types.Signature | None = None
class VerificationResult(DomainResourceR4):
    resourceType: Literal['VerificationResult']
    target: Annotated[list[fhir_types.Reference], Field(min_length=1)] | None = None
    targetLocation: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    need: fhir_types.CodeableConcept | None = None
    status: Literal['attested', 'in-process', 'req-revalid', 'reval-fail', 'val-fail', 'validated']
    statusDate: FHIRDateTime | None = None
    validationType: fhir_types.CodeableConcept | None = None
    validationProcess: Annotated[list[fhir_types.CodeableConcept], Field(min_length=1)] | None = None
    frequency: fhir_types.Timing | None = None
    lastPerformed: FHIRDateTime | None = None
    nextScheduled: FHIRDate | None = None
    failureAction: fhir_types.CodeableConcept | None = None
    primarySource: Annotated[list[VerificationResultPrimarySource], Field(min_length=1)] | None = None
    attestation: VerificationResultAttestation | None = None
    validator: Annotated[list[VerificationResultValidator], Field(min_length=1)] | None = None

class VisionPrescriptionLensSpecificationPrism(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    amount: FHIRDecimal
    base: Literal['down', 'in', 'out', 'up']
class VisionPrescriptionLensSpecification(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None
    product: fhir_types.CodeableConcept
    eye: Literal['left', 'right']
    sphere: FHIRDecimal | None = None
    cylinder: FHIRDecimal | None = None
    axis: FHIRInteger | None = None
    prism: Annotated[list[VisionPrescriptionLensSpecificationPrism], Field(min_length=1)] | None = None
    add: FHIRDecimal | None = None
    power: FHIRDecimal | None = None
    backCurve: FHIRDecimal | None = None
    diameter: FHIRDecimal | None = None
    duration: fhir_types.SimpleQuantity | None = None
    color: StrictStr | None = None
    brand: StrictStr | None = None
    note: Annotated[list[fhir_types.Annotation], Field(min_length=1)] | None = None
class VisionPrescription(DomainResourceR4):
    resourceType: Literal['VisionPrescription']
    identifier: Annotated[list[fhir_types.Identifier], Field(min_length=1)] | None = None
    status: Literal['active', 'cancelled', 'draft', 'entered-in-error']
    created: FHIRDateTime
    patient: fhir_types.Reference
    encounter: fhir_types.Reference | None = None
    dateWritten: FHIRDateTime
    prescriber: fhir_types.Reference
    lensSpecification: Annotated[list[VisionPrescriptionLensSpecification], Field(min_length=1)]

RESOURCE_MODELS: dict[str, type[FHIRBaseModel]] = {
    'Account': Account,
    'ActivityDefinition': ActivityDefinition,
    'AdverseEvent': AdverseEvent,
    'AllergyIntolerance': AllergyIntolerance,
    'Appointment': Appointment,
    'AppointmentResponse': AppointmentResponse,
    'AuditEvent': AuditEvent,
    'Basic': Basic,
    'Binary': Binary,
    'BiologicallyDerivedProduct': BiologicallyDerivedProduct,
    'BodyStructure': BodyStructure,
    'Bundle': Bundle,
    'CapabilityStatement': CapabilityStatement,
    'CarePlan': CarePlan,
    'CareTeam': CareTeam,
    'CatalogEntry': CatalogEntry,
    'ChargeItem': ChargeItem,
    'ChargeItemDefinition': ChargeItemDefinition,
    'Claim': Claim,
    'ClaimResponse': ClaimResponse,
    'ClinicalImpression': ClinicalImpression,
    'CodeSystem': CodeSystem,
    'Communication': Communication,
    'CommunicationRequest': CommunicationRequest,
    'CompartmentDefinition': CompartmentDefinition,
    'Composition': Composition,
    'ConceptMap': ConceptMap,
    'Condition': Condition,
    'Consent': Consent,
    'Contract': Contract,
    'Coverage': Coverage,
    'CoverageEligibilityRequest': CoverageEligibilityRequest,
    'CoverageEligibilityResponse': CoverageEligibilityResponse,
    'DetectedIssue': DetectedIssue,
    'Device': Device,
    'DeviceDefinition': DeviceDefinition,
    'DeviceMetric': DeviceMetric,
    'DeviceRequest': DeviceRequest,
    'DeviceUseStatement': DeviceUseStatement,
    'DiagnosticReport': DiagnosticReport,
    'DocumentManifest': DocumentManifest,
    'DocumentReference': DocumentReference,
    'EffectEvidenceSynthesis': EffectEvidenceSynthesis,
    'Encounter': Encounter,
    'Endpoint': Endpoint,
    'EnrollmentRequest': EnrollmentRequest,
    'EnrollmentResponse': EnrollmentResponse,
    'EpisodeOfCare': EpisodeOfCare,
    'EventDefinition': EventDefinition,
    'Evidence': Evidence,
    'EvidenceVariable': EvidenceVariable,
    'ExampleScenario': ExampleScenario,
    'ExplanationOfBenefit': ExplanationOfBenefit,
    'FamilyMemberHistory': FamilyMemberHistory,
    'Flag': Flag,
    'Goal': Goal,
    'GraphDefinition': GraphDefinition,
    'Group': Group,
    'GuidanceResponse': GuidanceResponse,
    'HealthcareService': HealthcareService,
    'ImagingStudy': ImagingStudy,
    'Immunization': Immunization,
    'ImmunizationEvaluation': ImmunizationEvaluation,
    'ImmunizationRecommendation': ImmunizationRecommendation,
    'ImplementationGuide': ImplementationGuide,
    'InsurancePlan': InsurancePlan,
    'Invoice': Invoice,
    'Library': Library,
    'Linkage': Linkage,
    'List': List,
    'Location': Location,
    'Measure': Measure,
    'MeasureReport': MeasureReport,
    'Media': Media,
    'Medication': Medication,
    'MedicationAdministration': MedicationAdministration,
    'MedicationDispense': MedicationDispense,
    'MedicationKnowledge': MedicationKnowledge,
    'MedicationRequest': MedicationRequest,
    'MedicationStatement': MedicationStatement,
    'MedicinalProduct': MedicinalProduct,
    'MedicinalProductAuthorization': MedicinalProductAuthorization,
    'MedicinalProductContraindication': MedicinalProductContraindication,
    'MedicinalProductIndication': MedicinalProductIndication,
    'MedicinalProductIngredient': MedicinalProductIngredient,
    'MedicinalProductInteraction': MedicinalProductInteraction,
    'MedicinalProductManufactured': MedicinalProductManufactured,
    'MedicinalProductPackaged': MedicinalProductPackaged,
    'MedicinalProductPharmaceutical': MedicinalProductPharmaceutical,
    'MedicinalProductUndesirableEffect': MedicinalProductUndesirableEffect,
    'MessageDefinition': MessageDefinition,
    'MessageHeader': MessageHeader,
    'MolecularSequence': MolecularSequence,
    'NamingSystem': NamingSystem,
    'NutritionOrder': NutritionOrder,
    'Observation': Observation,
    'ObservationDefinition': ObservationDefinition,
    'OperationDefinition': OperationDefinition,
    'OperationOutcome': OperationOutcome,
    'Organization': Organization,
    'OrganizationAffiliation': OrganizationAffiliation,
    'Parameters': Parameters,
    'Patient': Patient,
    'PaymentNotice': PaymentNotice,
    'PaymentReconciliation': PaymentReconciliation,
    'Person': Person,
    'PlanDefinition': PlanDefinition,
    'Practitioner': Practitioner,
    'PractitionerRole': PractitionerRole,
    'Procedure': Procedure,
    'Provenance': Provenance,
    'Questionnaire': Questionnaire,
    'QuestionnaireResponse': QuestionnaireResponse,
    'RelatedPerson': RelatedPerson,
    'RequestGroup': RequestGroup,
    'ResearchDefinition': ResearchDefinition,
    'ResearchElementDefinition': ResearchElementDefinition,
    'ResearchStudy': ResearchStudy,
    'ResearchSubject': ResearchSubject,
    'RiskAssessment': RiskAssessment,
    'RiskEvidenceSynthesis': RiskEvidenceSynthesis,
    'Schedule': Schedule,
    'SearchParameter': SearchParameter,
    'ServiceRequest': ServiceRequest,
    'Slot': Slot,
    'Specimen': Specimen,
    'SpecimenDefinition': SpecimenDefinition,
    'StructureDefinition': StructureDefinition,
    'StructureMap': StructureMap,
    'Subscription': Subscription,
    'Substance': Substance,
    'SubstanceNucleicAcid': SubstanceNucleicAcid,
    'SubstancePolymer': SubstancePolymer,
    'SubstanceProtein': SubstanceProtein,
    'SubstanceReferenceInformation': SubstanceReferenceInformation,
    'SubstanceSourceMaterial': SubstanceSourceMaterial,
    'SubstanceSpecification': SubstanceSpecification,
    'SupplyDelivery': SupplyDelivery,
    'SupplyRequest': SupplyRequest,
    'Task': Task,
    'TerminologyCapabilities': TerminologyCapabilities,
    'TestReport': TestReport,
    'TestScript': TestScript,
    'ValueSet': ValueSet,
    'VerificationResult': VerificationResult,
    'VisionPrescription': VisionPrescription,
}
Account.model_rebuild()
ActivityDefinition.model_rebuild()
AdverseEvent.model_rebuild()
AllergyIntolerance.model_rebuild()
Appointment.model_rebuild()
AppointmentResponse.model_rebuild()
AuditEvent.model_rebuild()
Basic.model_rebuild()
Binary.model_rebuild()
BiologicallyDerivedProduct.model_rebuild()
BodyStructure.model_rebuild()
Bundle.model_rebuild()
CapabilityStatement.model_rebuild()
CarePlan.model_rebuild()
CareTeam.model_rebuild()
CatalogEntry.model_rebuild()
ChargeItem.model_rebuild()
ChargeItemDefinition.model_rebuild()
Claim.model_rebuild()
ClaimResponse.model_rebuild()
ClinicalImpression.model_rebuild()
CodeSystem.model_rebuild()
Communication.model_rebuild()
CommunicationRequest.model_rebuild()
CompartmentDefinition.model_rebuild()
Composition.model_rebuild()
ConceptMap.model_rebuild()
Condition.model_rebuild()
Consent.model_rebuild()
Contract.model_rebuild()
Coverage.model_rebuild()
CoverageEligibilityRequest.model_rebuild()
CoverageEligibilityResponse.model_rebuild()
DetectedIssue.model_rebuild()
Device.model_rebuild()
DeviceDefinition.model_rebuild()
DeviceMetric.model_rebuild()
DeviceRequest.model_rebuild()
DeviceUseStatement.model_rebuild()
DiagnosticReport.model_rebuild()
DocumentManifest.model_rebuild()
DocumentReference.model_rebuild()
EffectEvidenceSynthesis.model_rebuild()
Encounter.model_rebuild()
Endpoint.model_rebuild()
EnrollmentRequest.model_rebuild()
EnrollmentResponse.model_rebuild()
EpisodeOfCare.model_rebuild()
EventDefinition.model_rebuild()
Evidence.model_rebuild()
EvidenceVariable.model_rebuild()
ExampleScenario.model_rebuild()
ExplanationOfBenefit.model_rebuild()
FamilyMemberHistory.model_rebuild()
Flag.model_rebuild()
Goal.model_rebuild()
GraphDefinition.model_rebuild()
Group.model_rebuild()
GuidanceResponse.model_rebuild()
HealthcareService.model_rebuild()
ImagingStudy.model_rebuild()
Immunization.model_rebuild()
ImmunizationEvaluation.model_rebuild()
ImmunizationRecommendation.model_rebuild()
ImplementationGuide.model_rebuild()
InsurancePlan.model_rebuild()
Invoice.model_rebuild()
Library.model_rebuild()
Linkage.model_rebuild()
List.model_rebuild()
Location.model_rebuild()
Measure.model_rebuild()
MeasureReport.model_rebuild()
Media.model_rebuild()
Medication.model_rebuild()
MedicationAdministration.model_rebuild()
MedicationDispense.model_rebuild()
MedicationKnowledge.model_rebuild()
MedicationRequest.model_rebuild()
MedicationStatement.model_rebuild()
MedicinalProduct.model_rebuild()
MedicinalProductAuthorization.model_rebuild()
MedicinalProductContraindication.model_rebuild()
MedicinalProductIndication.model_rebuild()
MedicinalProductIngredient.model_rebuild()
MedicinalProductInteraction.model_rebuild()
MedicinalProductManufactured.model_rebuild()
MedicinalProductPackaged.model_rebuild()
MedicinalProductPharmaceutical.model_rebuild()
MedicinalProductUndesirableEffect.model_rebuild()
MessageDefinition.model_rebuild()
MessageHeader.model_rebuild()
MolecularSequence.model_rebuild()
NamingSystem.model_rebuild()
NutritionOrder.model_rebuild()
Observation.model_rebuild()
ObservationDefinition.model_rebuild()
OperationDefinition.model_rebuild()
OperationOutcome.model_rebuild()
Organization.model_rebuild()
OrganizationAffiliation.model_rebuild()
Parameters.model_rebuild()
Patient.model_rebuild()
PaymentNotice.model_rebuild()
PaymentReconciliation.model_rebuild()
Person.model_rebuild()
PlanDefinition.model_rebuild()
Practitioner.model_rebuild()
PractitionerRole.model_rebuild()
Procedure.model_rebuild()
Provenance.model_rebuild()
Questionnaire.model_rebuild()
QuestionnaireResponse.model_rebuild()
RelatedPerson.model_rebuild()
RequestGroup.model_rebuild()
ResearchDefinition.model_rebuild()
ResearchElementDefinition.model_rebuild()
ResearchStudy.model_rebuild()
ResearchSubject.model_rebuild()
RiskAssessment.model_rebuild()
RiskEvidenceSynthesis.model_rebuild()
Schedule.model_rebuild()
SearchParameter.model_rebuild()
ServiceRequest.model_rebuild()
Slot.model_rebuild()
Specimen.model_rebuild()
SpecimenDefinition.model_rebuild()
StructureDefinition.model_rebuild()
StructureMap.model_rebuild()
Subscription.model_rebuild()
Substance.model_rebuild()
SubstanceNucleicAcid.model_rebuild()
SubstancePolymer.model_rebuild()
SubstanceProtein.model_rebuild()
SubstanceReferenceInformation.model_rebuild()
SubstanceSourceMaterial.model_rebuild()
SubstanceSpecification.model_rebuild()
SupplyDelivery.model_rebuild()
SupplyRequest.model_rebuild()
Task.model_rebuild()
TerminologyCapabilities.model_rebuild()
TestReport.model_rebuild()
TestScript.model_rebuild()
ValueSet.model_rebuild()
VerificationResult.model_rebuild()
VisionPrescription.model_rebuild()
