library package SYSMOD {
    doc
    /* Definition of SYSMOD Concepts for SysML v2
     *
     * Version v5.1alpha 
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
     * Copyright 2025, MBSE4U
     */
    occurrence def Project {
        doc
        /* The Project provides the context for the main engineering artifacts and sets cross relationships. */
        part brownfieldSystemContext : SystemContext;
        part projectStakeholders : Stakeholder [1..*];
        requirement problemStatement {
            subject system :> brownfieldSystemContext.soi;
        }
        part systemIdeaContext :> brownfieldSystemContext {
            part <soi> systemOfInterest :>> soi {
                satisfy problemStatement;
            }
        }
        part requirementSystemContext :> systemIdeaContext;
        requirement systemRequirementSpecification {
            subject system :> requirementSystemContext.soi;
        }
        #RequirementDerivation::derivation connection {
            end #RequirementDerivation::original ::> problemStatement;
            end #RequirementDerivation::derive ::> systemRequirementSpecification;
        }
        part systemContext :> requirementSystemContext {
            part <soi> systemOfInterest :>> soi {
                satisfy systemRequirementSpecification;
            }
        }
        part functionalContext :> systemContext;
        part logicalContext :> systemContext;
        part productContext :> systemContext;
    }
    occurrence projects : Project [*] nonunique;
    part def SystemContext {
        doc
        /* The System Context includes all system actors, the system of interest, 
         * and the relationships between the actors and the system.
         */
        part actors [1..*];
        part <soi> systemOfInterest;
        connection act2sys [1..*] {
            end [1] part 'actor' ::> actors;
            end [1] part soi ::> soi;
        }
        use case useCases [0..*] {
            subject theSubject :> soi;
        }
    }
    part systemContexts : SystemContext [*] nonunique;
    part def Stakeholder {
        doc
        /* SYSMOD-specific definition of the stakeholder concept */
        attribute risk : PriorityKind;
        attribute effort : PriorityKind;
        attribute contact : ScalarValues::String;
        attribute categories : StakeholderCategoryKind [*];
    }
    part stakeholders : Stakeholder [*] nonunique;
    enum def PriorityKind :> ScalarValues::Real {
        none = 0.0;
        low = 0.25;
        medium = 0.5;
        high = 0.75;
        critial = 1.0;
    }
    enum def StakeholderCategoryKind {
        Expert;
        RequirementOwner;
        User;
        Other;
    }
    requirement def SystemObjective {
        doc
        /* A goal that the system is aiming for. It does not have to be satisfied, 
         * but an evaluation must show that the system has brought the objective closer. 
         * Of course, it may also be satisfied.
         */
    }
    requirement systemObjectives : SystemObjective [*];
    concern def ExtendedConcern;
    concern extendedConcerns : ExtendedConcern [*] nonunique;
    requirement def ExtendedRequirement :> ExtendedConcern;
    requirement extendedRequirements : ExtendedRequirement [*] nonunique;
    metadata def <project> ProjectContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = projects meta SysML::Systems::OccurrenceUsage;
    }
    metadata def <systemContext> SystemContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemContexts meta SysML::Systems::PartUsage;
    }
    metadata def <exStakeholder> StakeholderMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = stakeholders meta SysML::Systems::PartUsage;
    }
    metadata def <systemObjective> SystemObjectiveMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemObjectives meta SysML::Systems::RequirementUsage;
    }
    metadata def <extendedConcern> ExtendedConcernMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = extendedConcerns meta SysML::Systems::RequirementUsage;
    }
    metadata def <extendedRequirement> ExtendedRequirementMetadata
        :> Metaobjects::SemanticMetadata {
        :>> baseType = extendedRequirements meta SysML::Systems::RequirementUsage;
    }
}
