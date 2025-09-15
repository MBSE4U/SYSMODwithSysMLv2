//
// Library SYSMOD - The Systems Modeling Toolbox
//
// The library provides concepts of the common and general purpose MBSE methodology SYSMOD.
// 
// Version: v5.0alpha (v4.x are SYSMOD for SysML v1 versions); work in progress
// License: Apache-2.0
// Maintainer: MBSE4U, Tim Weilkiens, Contact: tim@mbse4u.com
// Website: https://mbse4u.com/sysmod
// Topic: MBSE, Methodology
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Copyright 2025 MBSE4U
//
library package SYSMOD {
    doc
    /*
     * Definition of SYSMOD Concepts for SysML v2
     *
     * Version v5.0alpha 
     *
     * Copyright 2025, MBSE4U
     *
     */
    abstract occurrence def Project {
        doc /* The Project provides the context for the main engineering artifacts and builds the cross relationships. */

        //
        // Level -1
        //

        // Problem Space
        requirement problemStatement : ProblemStatement {
            subject :>> baseSystemContext.systemOfInterest;
        }
        part stakeholders[1..*] : Stakeholder;

        requirement requirementSpecification : ExtendedRequirement {
            subject :>> systemContext.systemOfInterest;
            require problemStatement;
        }

        // Solution Space
        part baseSystemContext : SystemContext;
        satisfy requirementSpecification by baseSystemContext.systemOfInterest;

        //
        // Level 0
        //

        // Problem Space
        part requirementSystemContext :> systemContext;
        requirement systemRequirementSpecification :> requirementSpecification {
            subject :>> requirementSystemContext.systemOfInterest;
        }

        // Solution Space
        part systemContext :> baseSystemContext;
        satisfy systemRequirementSpecification by systemContext.systemOfInterest;
    }
    occurrence projects[*] : Project;

    abstract part def SystemContext {
        doc /*
             * The System Context includes all system actors, the system of interest, 
             * and the relationships between the actors and the system.
             */
        part actors[*];
        part systemOfInterest : SystemPart;
    }
    part systemContexts[*] : SystemContext;

    abstract part def SystemPart {
        attribute maturity : MaturityKind default initial;
        attribute totalMaturity = (RealFunctions::sum(systemParts.maturity) + maturity) 
                                / (CollectionFunctions::size(systemParts) + 1);
        part systemParts[*] :SystemPart :> subparts;
    }
    part systemParts[*] : SystemPart;

    abstract part def MechanicalPart :> SystemPart;
    part mechanicalParts[*] : MechanicalPart :> systemParts;
    abstract part def ElectricalPart :> SystemPart;
    part electricalParts[*] : ElectricalPart :> systemParts;
    abstract part def SoftwarePart :> SystemPart;
    part softwareParts[*] : SoftwarePart :> systemParts;

    enum def MaturityKind :> ScalarValues::Real {
        final = 1;
        complete = 0.75;
        inProgress = 0.5;
        started = 0.25;
        initial = 0;
    }

    abstract part def Stakeholder {
        doc /* SYSMOD-specific definition of the stakeholder concept */
        attribute risk : PriorityKind;
        attribute effort : PriorityKind;
        attribute contact : ScalarValues::String;
        attribute categories[*] : StakeholderCategoryKind;
    }
    part stakeholders[*] : Stakeholder;
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

    abstract requirement def ProblemStatement {
        doc /* The problem that is to be solved by the system. */
        assert constraint {
            SequenceFunctions::size(stakeholders) > 0 
        }
    }
    requirement problemStatements[*] : ProblemStatement;

    abstract requirement def SystemObjective {
        doc /*
             * A goal that the system is aiming for. It does not have to be satisfied, 
             * but an evaluation must show that the system has brought the objective closer. 
             * Of course, it may also be satisfied.
             */
    }
    requirement systemObjectives[*] : SystemObjective;

    abstract requirement def ExtendedRequirement {
        // tbd
    }
    requirement extendedRequirements[*] : ExtendedRequirement;
}

library package SYSMOD_Metadata {

    private import SYSMOD::*;
    //
    // Semantic Metadata
    //
    metadata def <project> ProjectContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = projects meta SysML::PartUsage;
    }   
    metadata def <systemContext> SystemContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemContexts meta SysML::PartUsage;
    }   
    metadata def <systemPart> SystemPartMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemParts meta SysML::PartUsage;
    }
    metadata def <mechanicalPart> MechanicalPartMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = mechanicalParts meta SysML::PartUsage;
    }
    metadata def <electricalPart> ElectricalPartMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = electricalParts meta SysML::PartUsage;
    }
    metadata def <softwarePart> SoftwarePartMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = softwareParts meta SysML::PartUsage;
    }
    metadata def <exStakeholder> StakeholderMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = stakeholders meta SysML::PartUsage;
    }   
    metadata def <problemStatement> ProblemStatementMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = problemStatements meta SysML::RequirementUsage;
    }   
    metadata def <systemObjective> SystemObjectiveMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemObjectives meta SysML::RequirementUsage;
    }   
    metadata def <extendedRequirement> ExtendedRequirementMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = extendedRequirements meta SysML::RequirementUsage;
    }
}

package SYSMOD_Process {

    action def 'Standard SYSMOD Process' {
        first start;
        then action analyzeTheProblem : 'Analyze the Problem';
    }
    action def 'Analyze the Problem' {
        out requirement problemStatement : SYSMOD::ProblemStatement;
    }
    action def 'Specify the System Idea and System Objectives' {
        out part systemIdea;
        out requirement systemObjectives[*];
    }
}
