"""Generated FHIR R4 complex datatypes (39 base types)."""
from __future__ import annotations
from typing import Annotated, Any, Literal
from pydantic import Field, StrictBool, StrictStr, model_validator
from fhirlance.base import (
    ExtensionBase, FHIRBaseModel, FHIRCode, FHIRDate, FHIRDateTime, FHIRDecimal,
    FHIRId, FHIRInstant, FHIRInteger, FHIRPositiveInt, FHIRTime, FHIRUnsignedInt,
)

class Element(FHIRBaseModel):
    id: StrictStr | None = None
    extension: list[Any] | None = None

class Address(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    use: Literal['billing', 'home', 'old', 'temp', 'work'] | None = None
    type: Literal['both', 'physical', 'postal'] | None = None
    text: StrictStr | None = None
    line: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    city: StrictStr | None = None
    district: StrictStr | None = None
    state: StrictStr | None = None
    postalCode: StrictStr | None = None
    country: StrictStr | None = None
    period: Period | None = None

class Age(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    comparator: Literal['<', '<=', '>', '>='] | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

class Annotation(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    authorReference: Reference | None = None
    authorString: StrictStr | None = None
    time: FHIRDateTime | None = None
    text: StrictStr

    @model_validator(mode='after')
    def _check_choices(self) -> 'Annotation':
        _present = sum(1 for _f in ('authorReference', 'authorString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('author[x] allows at most one value')
        return self

class Attachment(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    contentType: FHIRCode | None = None
    language: FHIRCode | None = None
    data: StrictStr | None = None
    url: StrictStr | None = None
    size: FHIRUnsignedInt | None = None
    hash: StrictStr | None = None
    title: StrictStr | None = None
    creation: FHIRDateTime | None = None

class CodeableConcept(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    coding: Annotated[list[Coding], Field(min_length=1)] | None = None
    text: StrictStr | None = None

class Coding(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    system: StrictStr | None = None
    version: StrictStr | None = None
    code: FHIRCode | None = None
    display: StrictStr | None = None
    userSelected: StrictBool | None = None

class ContactDetail(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    name: StrictStr | None = None
    telecom: Annotated[list[ContactPoint], Field(min_length=1)] | None = None

class ContactPoint(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    system: Literal['email', 'fax', 'other', 'pager', 'phone', 'sms', 'url'] | None = None
    value: StrictStr | None = None
    use: Literal['home', 'mobile', 'old', 'temp', 'work'] | None = None
    rank: FHIRPositiveInt | None = None
    period: Period | None = None

class Contributor(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: Literal['author', 'editor', 'endorser', 'reviewer']
    name: StrictStr
    contact: Annotated[list[ContactDetail], Field(min_length=1)] | None = None

class Count(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    comparator: Literal['<', '<=', '>', '>='] | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

class DataRequirementCodeFilter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    path: StrictStr | None = None
    searchParam: StrictStr | None = None
    valueSet: StrictStr | None = None
    code: Annotated[list[Coding], Field(min_length=1)] | None = None
class DataRequirementDateFilter(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    path: StrictStr | None = None
    searchParam: StrictStr | None = None
    valueDateTime: FHIRDateTime | None = None
    valuePeriod: Period | None = None
    valueDuration: Duration | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DataRequirementDateFilter':
        _present = sum(1 for _f in ('valueDateTime', 'valuePeriod', 'valueDuration',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self
class DataRequirementSort(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    path: StrictStr
    direction: Literal['ascending', 'descending']
class DataRequirement(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: FHIRCode
    profile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    subjectCodeableConcept: CodeableConcept | None = None
    subjectReference: Reference | None = None
    mustSupport: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    codeFilter: Annotated[list[DataRequirementCodeFilter], Field(min_length=1)] | None = None
    dateFilter: Annotated[list[DataRequirementDateFilter], Field(min_length=1)] | None = None
    limit: FHIRPositiveInt | None = None
    sort: Annotated[list[DataRequirementSort], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DataRequirement':
        _present = sum(1 for _f in ('subjectCodeableConcept', 'subjectReference',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('subject[x] allows at most one value')
        return self

class Distance(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    comparator: Literal['<', '<=', '>', '>='] | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

class DosageDoseAndRate(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: CodeableConcept | None = None
    doseRange: Range | None = None
    doseQuantity: SimpleQuantity | None = None
    rateRatio: Ratio | None = None
    rateRange: Range | None = None
    rateQuantity: SimpleQuantity | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'DosageDoseAndRate':
        _present = sum(1 for _f in ('doseRange', 'doseQuantity',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('dose[x] allows at most one value')
        _present = sum(1 for _f in ('rateRatio', 'rateRange', 'rateQuantity',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('rate[x] allows at most one value')
        return self
class Dosage(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    sequence: FHIRInteger | None = None
    text: StrictStr | None = None
    additionalInstruction: Annotated[list[CodeableConcept], Field(min_length=1)] | None = None
    patientInstruction: StrictStr | None = None
    timing: Timing | None = None
    asNeededBoolean: StrictBool | None = None
    asNeededCodeableConcept: CodeableConcept | None = None
    site: CodeableConcept | None = None
    route: CodeableConcept | None = None
    method: CodeableConcept | None = None
    doseAndRate: Annotated[list[DosageDoseAndRate], Field(min_length=1)] | None = None
    maxDosePerPeriod: Ratio | None = None
    maxDosePerAdministration: SimpleQuantity | None = None
    maxDosePerLifetime: SimpleQuantity | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Dosage':
        _present = sum(1 for _f in ('asNeededBoolean', 'asNeededCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('asNeeded[x] allows at most one value')
        return self

class Duration(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    comparator: Literal['<', '<=', '>', '>='] | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

class ElementDefinitionSlicingDiscriminator(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: Literal['exists', 'pattern', 'profile', 'type', 'value']
    path: StrictStr
class ElementDefinitionSlicing(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    discriminator: Annotated[list[ElementDefinitionSlicingDiscriminator], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    ordered: StrictBool | None = None
    rules: Literal['closed', 'open', 'openAtEnd']
class ElementDefinitionBase(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    path: StrictStr
    min: FHIRUnsignedInt
    max: StrictStr
class ElementDefinitionType(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    code: StrictStr
    profile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    targetProfile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    aggregation: Annotated[list[Literal['bundled', 'contained', 'referenced']], Field(min_length=1)] | None = None
    versioning: Literal['either', 'independent', 'specific'] | None = None
class ElementDefinitionExample(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    label: StrictStr
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
    valueAddress: Address | None = None
    valueAge: Age | None = None
    valueAnnotation: Annotation | None = None
    valueAttachment: Attachment | None = None
    valueCodeableConcept: CodeableConcept | None = None
    valueCoding: Coding | None = None
    valueContactPoint: ContactPoint | None = None
    valueCount: Count | None = None
    valueDistance: Distance | None = None
    valueDuration: Duration | None = None
    valueHumanName: HumanName | None = None
    valueIdentifier: Identifier | None = None
    valueMoney: Money | None = None
    valuePeriod: Period | None = None
    valueQuantity: Quantity | None = None
    valueRange: Range | None = None
    valueRatio: Ratio | None = None
    valueReference: Reference | None = None
    valueSampledData: SampledData | None = None
    valueSignature: Signature | None = None
    valueTiming: Timing | None = None
    valueContactDetail: ContactDetail | None = None
    valueContributor: Contributor | None = None
    valueDataRequirement: DataRequirement | None = None
    valueExpression: Expression | None = None
    valueParameterDefinition: ParameterDefinition | None = None
    valueRelatedArtifact: RelatedArtifact | None = None
    valueTriggerDefinition: TriggerDefinition | None = None
    valueUsageContext: UsageContext | None = None
    valueDosage: Dosage | None = None
    valueMeta: Meta | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ElementDefinitionExample':
        _present = sum(1 for _f in ('valueBase64Binary', 'valueBoolean', 'valueCanonical', 'valueCode', 'valueDate', 'valueDateTime', 'valueDecimal', 'valueId', 'valueInstant', 'valueInteger', 'valueMarkdown', 'valueOid', 'valuePositiveInt', 'valueString', 'valueTime', 'valueUnsignedInt', 'valueUri', 'valueUrl', 'valueUuid', 'valueAddress', 'valueAge', 'valueAnnotation', 'valueAttachment', 'valueCodeableConcept', 'valueCoding', 'valueContactPoint', 'valueCount', 'valueDistance', 'valueDuration', 'valueHumanName', 'valueIdentifier', 'valueMoney', 'valuePeriod', 'valueQuantity', 'valueRange', 'valueRatio', 'valueReference', 'valueSampledData', 'valueSignature', 'valueTiming', 'valueContactDetail', 'valueContributor', 'valueDataRequirement', 'valueExpression', 'valueParameterDefinition', 'valueRelatedArtifact', 'valueTriggerDefinition', 'valueUsageContext', 'valueDosage', 'valueMeta',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self
class ElementDefinitionConstraint(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    key: FHIRId
    requirements: StrictStr | None = None
    severity: Literal['error', 'warning']
    human: StrictStr
    expression: StrictStr | None = None
    xpath: StrictStr | None = None
    source: StrictStr | None = None
class ElementDefinitionBinding(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    strength: Literal['example', 'extensible', 'preferred', 'required']
    description: StrictStr | None = None
    valueSet: StrictStr | None = None
class ElementDefinitionMapping(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    identity: FHIRId
    language: FHIRCode | None = None
    map: StrictStr
    comment: StrictStr | None = None
class ElementDefinition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    path: StrictStr
    representation: Annotated[list[Literal['cdaText', 'typeAttr', 'xhtml', 'xmlAttr', 'xmlText']], Field(min_length=1)] | None = None
    sliceName: StrictStr | None = None
    sliceIsConstraining: StrictBool | None = None
    label: StrictStr | None = None
    code: Annotated[list[Coding], Field(min_length=1)] | None = None
    slicing: ElementDefinitionSlicing | None = None
    short: StrictStr | None = None
    definition: StrictStr | None = None
    comment: StrictStr | None = None
    requirements: StrictStr | None = None
    alias: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    min: FHIRUnsignedInt | None = None
    max: StrictStr | None = None
    base: ElementDefinitionBase | None = None
    contentReference: StrictStr | None = None
    type: Annotated[list[ElementDefinitionType], Field(min_length=1)] | None = None
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
    defaultValueAddress: Address | None = None
    defaultValueAge: Age | None = None
    defaultValueAnnotation: Annotation | None = None
    defaultValueAttachment: Attachment | None = None
    defaultValueCodeableConcept: CodeableConcept | None = None
    defaultValueCoding: Coding | None = None
    defaultValueContactPoint: ContactPoint | None = None
    defaultValueCount: Count | None = None
    defaultValueDistance: Distance | None = None
    defaultValueDuration: Duration | None = None
    defaultValueHumanName: HumanName | None = None
    defaultValueIdentifier: Identifier | None = None
    defaultValueMoney: Money | None = None
    defaultValuePeriod: Period | None = None
    defaultValueQuantity: Quantity | None = None
    defaultValueRange: Range | None = None
    defaultValueRatio: Ratio | None = None
    defaultValueReference: Reference | None = None
    defaultValueSampledData: SampledData | None = None
    defaultValueSignature: Signature | None = None
    defaultValueTiming: Timing | None = None
    defaultValueContactDetail: ContactDetail | None = None
    defaultValueContributor: Contributor | None = None
    defaultValueDataRequirement: DataRequirement | None = None
    defaultValueExpression: Expression | None = None
    defaultValueParameterDefinition: ParameterDefinition | None = None
    defaultValueRelatedArtifact: RelatedArtifact | None = None
    defaultValueTriggerDefinition: TriggerDefinition | None = None
    defaultValueUsageContext: UsageContext | None = None
    defaultValueDosage: Dosage | None = None
    defaultValueMeta: Meta | None = None
    meaningWhenMissing: StrictStr | None = None
    orderMeaning: StrictStr | None = None
    fixedBase64Binary: StrictStr | None = None
    fixedBoolean: StrictBool | None = None
    fixedCanonical: StrictStr | None = None
    fixedCode: FHIRCode | None = None
    fixedDate: FHIRDate | None = None
    fixedDateTime: FHIRDateTime | None = None
    fixedDecimal: FHIRDecimal | None = None
    fixedId: FHIRId | None = None
    fixedInstant: FHIRInstant | None = None
    fixedInteger: FHIRInteger | None = None
    fixedMarkdown: StrictStr | None = None
    fixedOid: StrictStr | None = None
    fixedPositiveInt: FHIRPositiveInt | None = None
    fixedString: StrictStr | None = None
    fixedTime: FHIRTime | None = None
    fixedUnsignedInt: FHIRUnsignedInt | None = None
    fixedUri: StrictStr | None = None
    fixedUrl: StrictStr | None = None
    fixedUuid: StrictStr | None = None
    fixedAddress: Address | None = None
    fixedAge: Age | None = None
    fixedAnnotation: Annotation | None = None
    fixedAttachment: Attachment | None = None
    fixedCodeableConcept: CodeableConcept | None = None
    fixedCoding: Coding | None = None
    fixedContactPoint: ContactPoint | None = None
    fixedCount: Count | None = None
    fixedDistance: Distance | None = None
    fixedDuration: Duration | None = None
    fixedHumanName: HumanName | None = None
    fixedIdentifier: Identifier | None = None
    fixedMoney: Money | None = None
    fixedPeriod: Period | None = None
    fixedQuantity: Quantity | None = None
    fixedRange: Range | None = None
    fixedRatio: Ratio | None = None
    fixedReference: Reference | None = None
    fixedSampledData: SampledData | None = None
    fixedSignature: Signature | None = None
    fixedTiming: Timing | None = None
    fixedContactDetail: ContactDetail | None = None
    fixedContributor: Contributor | None = None
    fixedDataRequirement: DataRequirement | None = None
    fixedExpression: Expression | None = None
    fixedParameterDefinition: ParameterDefinition | None = None
    fixedRelatedArtifact: RelatedArtifact | None = None
    fixedTriggerDefinition: TriggerDefinition | None = None
    fixedUsageContext: UsageContext | None = None
    fixedDosage: Dosage | None = None
    fixedMeta: Meta | None = None
    patternBase64Binary: StrictStr | None = None
    patternBoolean: StrictBool | None = None
    patternCanonical: StrictStr | None = None
    patternCode: FHIRCode | None = None
    patternDate: FHIRDate | None = None
    patternDateTime: FHIRDateTime | None = None
    patternDecimal: FHIRDecimal | None = None
    patternId: FHIRId | None = None
    patternInstant: FHIRInstant | None = None
    patternInteger: FHIRInteger | None = None
    patternMarkdown: StrictStr | None = None
    patternOid: StrictStr | None = None
    patternPositiveInt: FHIRPositiveInt | None = None
    patternString: StrictStr | None = None
    patternTime: FHIRTime | None = None
    patternUnsignedInt: FHIRUnsignedInt | None = None
    patternUri: StrictStr | None = None
    patternUrl: StrictStr | None = None
    patternUuid: StrictStr | None = None
    patternAddress: Address | None = None
    patternAge: Age | None = None
    patternAnnotation: Annotation | None = None
    patternAttachment: Attachment | None = None
    patternCodeableConcept: CodeableConcept | None = None
    patternCoding: Coding | None = None
    patternContactPoint: ContactPoint | None = None
    patternCount: Count | None = None
    patternDistance: Distance | None = None
    patternDuration: Duration | None = None
    patternHumanName: HumanName | None = None
    patternIdentifier: Identifier | None = None
    patternMoney: Money | None = None
    patternPeriod: Period | None = None
    patternQuantity: Quantity | None = None
    patternRange: Range | None = None
    patternRatio: Ratio | None = None
    patternReference: Reference | None = None
    patternSampledData: SampledData | None = None
    patternSignature: Signature | None = None
    patternTiming: Timing | None = None
    patternContactDetail: ContactDetail | None = None
    patternContributor: Contributor | None = None
    patternDataRequirement: DataRequirement | None = None
    patternExpression: Expression | None = None
    patternParameterDefinition: ParameterDefinition | None = None
    patternRelatedArtifact: RelatedArtifact | None = None
    patternTriggerDefinition: TriggerDefinition | None = None
    patternUsageContext: UsageContext | None = None
    patternDosage: Dosage | None = None
    patternMeta: Meta | None = None
    example: Annotated[list[ElementDefinitionExample], Field(min_length=1)] | None = None
    minValueDate: FHIRDate | None = None
    minValueDateTime: FHIRDateTime | None = None
    minValueInstant: FHIRInstant | None = None
    minValueTime: FHIRTime | None = None
    minValueDecimal: FHIRDecimal | None = None
    minValueInteger: FHIRInteger | None = None
    minValuePositiveInt: FHIRPositiveInt | None = None
    minValueUnsignedInt: FHIRUnsignedInt | None = None
    minValueQuantity: Quantity | None = None
    maxValueDate: FHIRDate | None = None
    maxValueDateTime: FHIRDateTime | None = None
    maxValueInstant: FHIRInstant | None = None
    maxValueTime: FHIRTime | None = None
    maxValueDecimal: FHIRDecimal | None = None
    maxValueInteger: FHIRInteger | None = None
    maxValuePositiveInt: FHIRPositiveInt | None = None
    maxValueUnsignedInt: FHIRUnsignedInt | None = None
    maxValueQuantity: Quantity | None = None
    maxLength: FHIRInteger | None = None
    condition: Annotated[list[FHIRId], Field(min_length=1)] | None = None
    constraint: Annotated[list[ElementDefinitionConstraint], Field(min_length=1)] | None = None
    mustSupport: StrictBool | None = None
    isModifier: StrictBool | None = None
    isModifierReason: StrictStr | None = None
    isSummary: StrictBool | None = None
    binding: ElementDefinitionBinding | None = None
    mapping: Annotated[list[ElementDefinitionMapping], Field(min_length=1)] | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'ElementDefinition':
        _present = sum(1 for _f in ('defaultValueBase64Binary', 'defaultValueBoolean', 'defaultValueCanonical', 'defaultValueCode', 'defaultValueDate', 'defaultValueDateTime', 'defaultValueDecimal', 'defaultValueId', 'defaultValueInstant', 'defaultValueInteger', 'defaultValueMarkdown', 'defaultValueOid', 'defaultValuePositiveInt', 'defaultValueString', 'defaultValueTime', 'defaultValueUnsignedInt', 'defaultValueUri', 'defaultValueUrl', 'defaultValueUuid', 'defaultValueAddress', 'defaultValueAge', 'defaultValueAnnotation', 'defaultValueAttachment', 'defaultValueCodeableConcept', 'defaultValueCoding', 'defaultValueContactPoint', 'defaultValueCount', 'defaultValueDistance', 'defaultValueDuration', 'defaultValueHumanName', 'defaultValueIdentifier', 'defaultValueMoney', 'defaultValuePeriod', 'defaultValueQuantity', 'defaultValueRange', 'defaultValueRatio', 'defaultValueReference', 'defaultValueSampledData', 'defaultValueSignature', 'defaultValueTiming', 'defaultValueContactDetail', 'defaultValueContributor', 'defaultValueDataRequirement', 'defaultValueExpression', 'defaultValueParameterDefinition', 'defaultValueRelatedArtifact', 'defaultValueTriggerDefinition', 'defaultValueUsageContext', 'defaultValueDosage', 'defaultValueMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('defaultValue[x] allows at most one value')
        _present = sum(1 for _f in ('fixedBase64Binary', 'fixedBoolean', 'fixedCanonical', 'fixedCode', 'fixedDate', 'fixedDateTime', 'fixedDecimal', 'fixedId', 'fixedInstant', 'fixedInteger', 'fixedMarkdown', 'fixedOid', 'fixedPositiveInt', 'fixedString', 'fixedTime', 'fixedUnsignedInt', 'fixedUri', 'fixedUrl', 'fixedUuid', 'fixedAddress', 'fixedAge', 'fixedAnnotation', 'fixedAttachment', 'fixedCodeableConcept', 'fixedCoding', 'fixedContactPoint', 'fixedCount', 'fixedDistance', 'fixedDuration', 'fixedHumanName', 'fixedIdentifier', 'fixedMoney', 'fixedPeriod', 'fixedQuantity', 'fixedRange', 'fixedRatio', 'fixedReference', 'fixedSampledData', 'fixedSignature', 'fixedTiming', 'fixedContactDetail', 'fixedContributor', 'fixedDataRequirement', 'fixedExpression', 'fixedParameterDefinition', 'fixedRelatedArtifact', 'fixedTriggerDefinition', 'fixedUsageContext', 'fixedDosage', 'fixedMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('fixed[x] allows at most one value')
        _present = sum(1 for _f in ('patternBase64Binary', 'patternBoolean', 'patternCanonical', 'patternCode', 'patternDate', 'patternDateTime', 'patternDecimal', 'patternId', 'patternInstant', 'patternInteger', 'patternMarkdown', 'patternOid', 'patternPositiveInt', 'patternString', 'patternTime', 'patternUnsignedInt', 'patternUri', 'patternUrl', 'patternUuid', 'patternAddress', 'patternAge', 'patternAnnotation', 'patternAttachment', 'patternCodeableConcept', 'patternCoding', 'patternContactPoint', 'patternCount', 'patternDistance', 'patternDuration', 'patternHumanName', 'patternIdentifier', 'patternMoney', 'patternPeriod', 'patternQuantity', 'patternRange', 'patternRatio', 'patternReference', 'patternSampledData', 'patternSignature', 'patternTiming', 'patternContactDetail', 'patternContributor', 'patternDataRequirement', 'patternExpression', 'patternParameterDefinition', 'patternRelatedArtifact', 'patternTriggerDefinition', 'patternUsageContext', 'patternDosage', 'patternMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('pattern[x] allows at most one value')
        _present = sum(1 for _f in ('minValueDate', 'minValueDateTime', 'minValueInstant', 'minValueTime', 'minValueDecimal', 'minValueInteger', 'minValuePositiveInt', 'minValueUnsignedInt', 'minValueQuantity',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('minValue[x] allows at most one value')
        _present = sum(1 for _f in ('maxValueDate', 'maxValueDateTime', 'maxValueInstant', 'maxValueTime', 'maxValueDecimal', 'maxValueInteger', 'maxValuePositiveInt', 'maxValueUnsignedInt', 'maxValueQuantity',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('maxValue[x] allows at most one value')
        return self

class Expression(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    description: StrictStr | None = None
    name: FHIRId | None = None
    language: FHIRCode
    expression: StrictStr | None = None
    reference: StrictStr | None = None

class Extension(ExtensionBase):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    url: StrictStr
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
    valueAddress: Address | None = None
    valueAge: Age | None = None
    valueAnnotation: Annotation | None = None
    valueAttachment: Attachment | None = None
    valueCodeableConcept: CodeableConcept | None = None
    valueCoding: Coding | None = None
    valueContactPoint: ContactPoint | None = None
    valueCount: Count | None = None
    valueDistance: Distance | None = None
    valueDuration: Duration | None = None
    valueHumanName: HumanName | None = None
    valueIdentifier: Identifier | None = None
    valueMoney: Money | None = None
    valuePeriod: Period | None = None
    valueQuantity: Quantity | None = None
    valueRange: Range | None = None
    valueRatio: Ratio | None = None
    valueReference: Reference | None = None
    valueSampledData: SampledData | None = None
    valueSignature: Signature | None = None
    valueTiming: Timing | None = None
    valueContactDetail: ContactDetail | None = None
    valueContributor: Contributor | None = None
    valueDataRequirement: DataRequirement | None = None
    valueExpression: Expression | None = None
    valueParameterDefinition: ParameterDefinition | None = None
    valueRelatedArtifact: RelatedArtifact | None = None
    valueTriggerDefinition: TriggerDefinition | None = None
    valueUsageContext: UsageContext | None = None
    valueDosage: Dosage | None = None
    valueMeta: Meta | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Extension':
        _present = sum(1 for _f in ('valueBase64Binary', 'valueBoolean', 'valueCanonical', 'valueCode', 'valueDate', 'valueDateTime', 'valueDecimal', 'valueId', 'valueInstant', 'valueInteger', 'valueMarkdown', 'valueOid', 'valuePositiveInt', 'valueString', 'valueTime', 'valueUnsignedInt', 'valueUri', 'valueUrl', 'valueUuid', 'valueAddress', 'valueAge', 'valueAnnotation', 'valueAttachment', 'valueCodeableConcept', 'valueCoding', 'valueContactPoint', 'valueCount', 'valueDistance', 'valueDuration', 'valueHumanName', 'valueIdentifier', 'valueMoney', 'valuePeriod', 'valueQuantity', 'valueRange', 'valueRatio', 'valueReference', 'valueSampledData', 'valueSignature', 'valueTiming', 'valueContactDetail', 'valueContributor', 'valueDataRequirement', 'valueExpression', 'valueParameterDefinition', 'valueRelatedArtifact', 'valueTriggerDefinition', 'valueUsageContext', 'valueDosage', 'valueMeta',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('value[x] allows at most one value')
        return self

class HumanName(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    use: Literal['anonymous', 'maiden', 'nickname', 'official', 'old', 'temp', 'usual'] | None = None
    text: StrictStr | None = None
    family: StrictStr | None = None
    given: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    prefix: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    suffix: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    period: Period | None = None

class Identifier(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    use: Literal['official', 'old', 'secondary', 'temp', 'usual'] | None = None
    type: CodeableConcept | None = None
    system: StrictStr | None = None
    value: StrictStr | None = None
    period: Period | None = None
    assigner: Reference | None = None

class MarketingStatus(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    country: CodeableConcept
    jurisdiction: CodeableConcept | None = None
    status: CodeableConcept
    dateRange: Period
    restoreDate: FHIRDateTime | None = None

class Meta(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    versionId: FHIRId | None = None
    lastUpdated: FHIRInstant | None = None
    source: StrictStr | None = None
    profile: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    security: Annotated[list[Coding], Field(min_length=1)] | None = None
    tag: Annotated[list[Coding], Field(min_length=1)] | None = None

class Money(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    currency: FHIRCode | None = None

class Narrative(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    status: Literal['additional', 'empty', 'extensions', 'generated']
    div: StrictStr

class ParameterDefinition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    name: FHIRCode | None = None
    use: Literal['in', 'out']
    min: FHIRInteger | None = None
    max: StrictStr | None = None
    documentation: StrictStr | None = None
    type: FHIRCode
    profile: StrictStr | None = None

class Period(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    start: FHIRDateTime | None = None
    end: FHIRDateTime | None = None

class Population(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    ageRange: Range | None = None
    ageCodeableConcept: CodeableConcept | None = None
    gender: CodeableConcept | None = None
    race: CodeableConcept | None = None
    physiologicalCondition: CodeableConcept | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'Population':
        _present = sum(1 for _f in ('ageRange', 'ageCodeableConcept',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('age[x] allows at most one value')
        return self

class ProdCharacteristic(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    height: Quantity | None = None
    width: Quantity | None = None
    depth: Quantity | None = None
    weight: Quantity | None = None
    nominalVolume: Quantity | None = None
    externalDiameter: Quantity | None = None
    shape: StrictStr | None = None
    color: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    imprint: Annotated[list[StrictStr], Field(min_length=1)] | None = None
    image: Annotated[list[Attachment], Field(min_length=1)] | None = None
    scoring: CodeableConcept | None = None

class ProductShelfLife(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    identifier: Identifier | None = None
    type: CodeableConcept
    period: Quantity
    specialPrecautionsForStorage: Annotated[list[CodeableConcept], Field(min_length=1)] | None = None

class Quantity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    comparator: Literal['<', '<=', '>', '>='] | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

class Range(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    low: SimpleQuantity | None = None
    high: SimpleQuantity | None = None

class Ratio(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    numerator: Quantity | None = None
    denominator: Quantity | None = None

class Reference(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    reference: StrictStr | None = None
    type: StrictStr | None = None
    identifier: Identifier | None = None
    display: StrictStr | None = None

class RelatedArtifact(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: Literal['citation', 'composed-of', 'depends-on', 'derived-from', 'documentation', 'justification', 'predecessor', 'successor']
    label: StrictStr | None = None
    display: StrictStr | None = None
    citation: StrictStr | None = None
    url: StrictStr | None = None
    document: Attachment | None = None
    resource: StrictStr | None = None

class SampledData(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    origin: SimpleQuantity
    period: FHIRDecimal
    factor: FHIRDecimal | None = None
    lowerLimit: FHIRDecimal | None = None
    upperLimit: FHIRDecimal | None = None
    dimensions: FHIRPositiveInt
    data: StrictStr | None = None

class Signature(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: Annotated[list[Coding], Field(min_length=1)]
    when: FHIRInstant
    who: Reference
    onBehalfOf: Reference | None = None
    targetFormat: FHIRCode | None = None
    sigFormat: FHIRCode | None = None
    data: StrictStr | None = None

class SubstanceAmountReferenceRange(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    lowLimit: Quantity | None = None
    highLimit: Quantity | None = None
class SubstanceAmount(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    amountQuantity: Quantity | None = None
    amountRange: Range | None = None
    amountString: StrictStr | None = None
    amountType: CodeableConcept | None = None
    amountText: StrictStr | None = None
    referenceRange: SubstanceAmountReferenceRange | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'SubstanceAmount':
        _present = sum(1 for _f in ('amountQuantity', 'amountRange', 'amountString',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('amount[x] allows at most one value')
        return self

class TimingRepeat(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    boundsDuration: Duration | None = None
    boundsRange: Range | None = None
    boundsPeriod: Period | None = None
    count: FHIRPositiveInt | None = None
    countMax: FHIRPositiveInt | None = None
    duration: FHIRDecimal | None = None
    durationMax: FHIRDecimal | None = None
    durationUnit: Literal['a', 'd', 'h', 'min', 'mo', 's', 'wk'] | None = None
    frequency: FHIRPositiveInt | None = None
    frequencyMax: FHIRPositiveInt | None = None
    period: FHIRDecimal | None = None
    periodMax: FHIRDecimal | None = None
    periodUnit: Literal['a', 'd', 'h', 'min', 'mo', 's', 'wk'] | None = None
    dayOfWeek: Annotated[list[Literal['fri', 'mon', 'sat', 'sun', 'thu', 'tue', 'wed']], Field(min_length=1)] | None = None
    timeOfDay: Annotated[list[FHIRTime], Field(min_length=1)] | None = None
    when: Annotated[list[Literal['AC', 'ACD', 'ACM', 'ACV', 'AFT', 'AFT.early', 'AFT.late', 'C', 'CD', 'CM', 'CV', 'EVE', 'EVE.early', 'EVE.late', 'HS', 'MORN', 'MORN.early', 'MORN.late', 'NIGHT', 'NOON', 'PC', 'PCD', 'PCM', 'PCV', 'PHS', 'WAKE']], Field(min_length=1)] | None = None
    offset: FHIRUnsignedInt | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'TimingRepeat':
        _present = sum(1 for _f in ('boundsDuration', 'boundsRange', 'boundsPeriod',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('bounds[x] allows at most one value')
        return self
class Timing(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    modifierExtension: Annotated[list[Extension], Field(min_length=1)] | None = None
    event: Annotated[list[FHIRDateTime], Field(min_length=1)] | None = None
    repeat: TimingRepeat | None = None
    code: CodeableConcept | None = None

class TriggerDefinition(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    type: Literal['data-access-ended', 'data-accessed', 'data-added', 'data-changed', 'data-modified', 'data-removed', 'named-event', 'periodic']
    name: StrictStr | None = None
    timingTiming: Timing | None = None
    timingReference: Reference | None = None
    timingDate: FHIRDate | None = None
    timingDateTime: FHIRDateTime | None = None
    data: Annotated[list[DataRequirement], Field(min_length=1)] | None = None
    condition: Expression | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'TriggerDefinition':
        _present = sum(1 for _f in ('timingTiming', 'timingReference', 'timingDate', 'timingDateTime',) if getattr(self, _f) is not None)
        if _present > 1: raise ValueError('timing[x] allows at most one value')
        return self

class UsageContext(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    code: Coding
    valueCodeableConcept: CodeableConcept | None = None
    valueQuantity: Quantity | None = None
    valueRange: Range | None = None
    valueReference: Reference | None = None

    @model_validator(mode='after')
    def _check_choices(self) -> 'UsageContext':
        _present = sum(1 for _f in ('valueCodeableConcept', 'valueQuantity', 'valueRange', 'valueReference',) if getattr(self, _f) is not None)
        if _present != 1: raise ValueError('value[x] requires exactly one value')
        return self

class SimpleQuantity(FHIRBaseModel):
    id: StrictStr | None = None
    extension: Annotated[list[Extension], Field(min_length=1)] | None = None
    value: FHIRDecimal | None = None
    unit: StrictStr | None = None
    system: StrictStr | None = None
    code: FHIRCode | None = None

Address.model_rebuild()
Age.model_rebuild()
Annotation.model_rebuild()
Attachment.model_rebuild()
CodeableConcept.model_rebuild()
Coding.model_rebuild()
ContactDetail.model_rebuild()
ContactPoint.model_rebuild()
Contributor.model_rebuild()
Count.model_rebuild()
DataRequirement.model_rebuild()
Distance.model_rebuild()
Dosage.model_rebuild()
Duration.model_rebuild()
ElementDefinition.model_rebuild()
Expression.model_rebuild()
Extension.model_rebuild()
HumanName.model_rebuild()
Identifier.model_rebuild()
MarketingStatus.model_rebuild()
Meta.model_rebuild()
Money.model_rebuild()
Narrative.model_rebuild()
ParameterDefinition.model_rebuild()
Period.model_rebuild()
Population.model_rebuild()
ProdCharacteristic.model_rebuild()
ProductShelfLife.model_rebuild()
Quantity.model_rebuild()
Range.model_rebuild()
Ratio.model_rebuild()
Reference.model_rebuild()
RelatedArtifact.model_rebuild()
SampledData.model_rebuild()
Signature.model_rebuild()
SubstanceAmount.model_rebuild()
Timing.model_rebuild()
TriggerDefinition.model_rebuild()
UsageContext.model_rebuild()
SimpleQuantity.model_rebuild()
