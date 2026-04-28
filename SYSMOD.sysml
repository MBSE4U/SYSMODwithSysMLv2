library package SYSMOD {
    doc
    /* Definition of SYSMOD Concepts for SysML v2
     *
     * Version v5.1 
     *
     * Licensed under the Apache License, Version 2.0 (the "License");
     * you may not use this file except in compliance with the License.
     * You may obtain a copy of the License at
     *
     * http://www.apache.org/licenses/LICENSE-2.0
     *
     * Unless required by applicable law or agreed to in writing, software
     * distributed under the License is distributed on an "AS IS" BASIS,
     * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     * See the License for the specific language governing permissions and
     * limitations under the License.
     *
     * Copyright 2026, MBSE4U
     */

    //
    // SYSMOD Project which links all the main artifacts together within a shared context.
    //
    occurrence def Project {
        doc
        /* The Project provides a context for the engineering artifacts used for this specific project and sets cross relationships. */
        part projectOwner :> projectStakeholders {
            doc
            /* The Project Owner is a special Stakeholder who is in charge of the Project. */
            attribute :>> risk default LevelKind::critical;
            attribute :>> effort default LevelKind::low;
            attribute :>> categories default StakeholderCategoryKind::requirementOwner;
        }
        part brownfieldSystemContext : SystemContext {
            doc
            /* The Brownfield Context includes the system, its subcomponents, and actors that are already identified at the start of the Project. These constraints limit the set of possible solutions. */
        }
        part projectStakeholders : ExtendedStakeholder [0..*] {
            doc
            /* Stakeholders are individuals and organizations that have an interest in the system. They have needs and are potential sources of system requirements. */
        }
        concern problemStatement : ExtendedConcern {
            doc
            /* The Problem Statement is an elevator pitch that describes the problem the system of interest is intended to solve. It is based on the Brownfield system. The problem statement does not specify a solution. The project owner is the stakeholder of the problem statement. */
            subject brownfieldSystem :> brownfieldSystemContext.soi;
            stakeholder projectOwner :> Project::projectOwner;
            attribute :>> priority = LevelKind::critical;
        }
        concern stakeholderNeeds {
            doc
            /* The Stakeholder Needs is the root element for stakeholder needs which will be translated into system requirements. The needs are based on the brownfield system and frames the problem statement. */
            subject brownfieldSystem :> brownfieldSystemContext.soi;
            frame problemStatement;
        }
        part systemIdeaContext :> brownfieldSystemContext {
            doc
            /* The system idea context contains the system idea and additional actors, if necessary. It specializes the brownfield system context. */
            part :>> brownfieldSystemContext::soi {
                doc
                /* The system idea is the answer to the problem statement. It is a rough, elevator-pitch-style outline of the system designed to solve the problem. The system idea specializes the brownfield system. */
                satisfy Project::problemStatement;
            }
        }
        part specificationContext :> systemIdeaContext {
            doc
            /* The specification context includes the actors and the system, along with specific subcomponents, which are defined during the requirements analysis. The specification context is also the owner of the system use cases. The context specializes the system idea. */
        }
        requirement systemRequirementSpecification {
            doc
            /* The System Requirement Specification is the root element for system requirements. They frame the stakeholder needs. */
            subject specificationSystem :> specificationContext.soi;
            frame stakeholderNeeds;
        }
        part solutionContext :> specificationContext {
            doc
            /* The Solution Context specializes the specification context and is the base context for the solution context. */
            part solutionSystem :>> soi {
                doc
                /* The solution system specializes the specification system and is the base system for the solution. It satisfies the system requirements. */
                satisfy systemRequirementSpecification;
            }
        }
        part functionalContext :> solutionContext [0..1] {
            doc
            /* The Functional Context is optional and specializes the solution context and provides the context for a fcuntional architecture, for example, developed with the FAS method. */
            part functionalSystem {
                doc
                /* The Functional System is the root element of the functional architecture. It is part of the context in addition to the inherited solution system which may contain non-functional parts but is a reference for the functional architecture, such as owner of the functions. */
            }
        }
        part logicalContext :> solutionContext [0..1] {
            doc
            /* The Logical Context is optional and specializes the solution context and provides the context for a logical architecture. */
        }
        part productContext :> solutionContext {
            doc
            /* The Product Context specializes the solution context and provides the context for a product architecture. */
        }
        allocation functional2logical [0..1] allocate functionalContext to logicalContext;
        allocation logical2product [0..1] allocate logicalContext to productContext;
    }
    abstract occurrence projects : Project [*];

    //
    // SYSMOD System Context
    //
    part def SystemContext {
        doc
        /* The SYSMOD System Context includes all system actors, the system of interest, 
         * the relationships between the actors and the system, as well as the use cases.
         */
        part actors [1..*] {
            doc
            /* The actors of the system of interest, i.e., all external entities which interact with system including humans, external systems, and environmental effects. */
            port actorPort : ActorPort {
                doc
                /* Dedicated port of an actor to exchange items with the system. */
            }
        }
        part <soi> systemOfInterest {
            doc
            /* Black box system of interest. */
            port systemPort : SystemPort [*];
        }
        part <soiImpl> systemOfInterestImplementation :> soi {
            doc
            /* White box system of interest. */
        }
        interface act2sys : ActorSystemInterface [1..*] connect actors.actorPort to soi.systemPort {
            doc
            /* Set of all actor/system interfaces. */
        }
        use case useCases [0..*] {
            doc
            /* Set of all system use cases. */
            subject soi :> SystemContext::soi;
        }
    }
    abstract part systemContexts : SystemContext [*];

    interface def ActorSystemInterface {
        doc
        /* Common interface definition for the link between actors and the system of interest. */
        end [1..*] port actorPort : ActorPort;
        end [1] port systemPort : SystemPort;
    }
    port def ActorPort {
        doc
        /* Base port definition for actor ports. */
    }
    port def SystemPort {
        doc
        /* Base port definition for system ports. */
    }

    //
    // SYSMOD Stakeholder and Requirement Concepts
    //
    part def ExtendedStakeholder {
        doc
        /* SYSMOD-specific definition of a stakeholder concept */
        attribute risk : LevelKind default LevelKind::none {
            doc
            /* What is the risk of failure if I ignore this stakeholder? */
        }
        attribute effort : LevelKind default LevelKind::none {
            doc
            /* How much effort is involved in identifying this stakeholder's concerns and requirements? */
        }
        derived attribute priority : ScalarValues::Real = risk * effort {
            doc
            /* Priority is the product of risk and effort. */
        }
        attribute contact : ScalarValues::String [0..1] {
            doc
            /* Contact information of the stakeholder. */
        }
        attribute categories : StakeholderCategoryKind [*] {
            doc
            /* Stakeholder kinds */
        }
    }
    abstract part stakeholders : ExtendedStakeholder [*];

    enum def StakeholderCategoryKind {
        doc
        /* Different kinds of stakeholders. */
        expert;
        requirementOwner;
        user;
        other;
    }

    concern def ExtendedConcern {
        /* Base element for concerns. */
        attribute priority : LevelKind default LevelKind::none;
    }
    abstract concern extendedConcerns : ExtendedConcern [*];

    requirement def ExtendedRequirement :> ExtendedConcern {
        doc
        /* The extended requirement adds further features to the requirement model element. 
         * Typically, you would define your own set of features and not use the SYSMOD set only.
         */
        attribute obligation : ObligationKind default ObligationKind::none;
        attribute stability : StabilityKind default StabilityKind::none;
        attribute motivation : ScalarValues::String;
    }
    abstract requirement extendedRequirements : ExtendedRequirement [*];

    enum def ObligationKind {
        doc
        /* Enumeration for different kinds of obligations. */
        none;
        mandatory;
        optional;
    }
    enum def StabilityKind {
        doc
        /* Enumeration for stability kinds. */
        none;
        unstable;
        stable;
    }

    //
    // Common Concepts
    //
    enum def LevelKind :> ScalarValues::Real {
        doc
        /* Common enumeration of levels with real values, for example, for priority calculations. */
        none = 0.0;
        low = 0.25;
        medium = 0.5;
        high = 0.75;
        critical = 1.0;
    }

    //
    // Semantic Metadata
    //
    metadata def <project> ProjectMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = projects meta SysML::Type;
        :> annotatedElement : SysML::OccurrenceDefinition;
        :> annotatedElement : SysML::OccurrenceUsage;
    }
    metadata def <systemContext> SystemContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemContexts meta SysML::Type;
        :> annotatedElement : SysML::PartDefinition;
        :> annotatedElement : SysML::PartUsage;
    }
    metadata def <extendedStakeholder> StakeholderMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = stakeholders meta SysML::Type;
        :> annotatedElement : SysML::PartDefinition;
        :> annotatedElement : SysML::PartUsage;
    }
    metadata def <extendedConcern> ExtendedConcernMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = extendedConcerns meta SysML::Type;
        :> annotatedElement : SysML::ConcernDefinition;
        :> annotatedElement : SysML::ConcernUsage;
    }
    metadata def <extendedRequirement> ExtendedRequirementMetadata
        :> Metaobjects::SemanticMetadata {
        :>> baseType = extendedRequirements meta SysML::Type;
        :> annotatedElement : SysML::RequirementDefinition;
        :> annotatedElement : SysML::RequirementUsage;
    }
}
