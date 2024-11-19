// Copyright 2024 MBSE4U

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

library package SYSMOD {
    doc
    /*
     * Definition of SYSMOD Concepts
     *
     * Version 1.0beta 
     *
     * Copyright 2024, MBSE4U
     *
     */
    part def ProjectContext :> SystemContext {
        doc /*
             * The Project Context includes the system problem statement and corresponding stakeholders,
             * the initial version of the system of interest and potential system actors.
             */
        requirement problemStatement : ProblemStatement {
            subject :>> systemOfInterest;
        }
        part stakeholders[1..*] : Stakeholder;
    }
    part projectContexts[*] : ProjectContext;

    part def SystemContext {
        doc /*
             * The System Context includes all system actors, the system of interest, 
             * and the relationships between the actors and the system.
             */
        part actors[*];
        part systemOfInterest;
    }
    part systemContexts[*] : SystemContext;

    part def Stakeholder {
        doc /*
             * SYSMOD-specific definition of the stakeholder concept
             */
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

    requirement def ProblemStatement {
        doc /*
             * The problem that is to be solved by the system.
             */
        assert constraint {
            SequenceFunctions::size(stakeholders) > 0 
        }
    }
    requirement problemStatements[*] : ProblemStatement;


    //
    // Semantic Metadata
    //
    metadata def <projectContext> ProjectContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = projectContexts meta SysML::PartUsage;
    }   
    metadata def <systemContext> SystemContextMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = systemContexts meta SysML::PartUsage;
    }   
    metadata def <extStakeholder> StakeholderMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = extStakeholder meta SysML::PartUsage;
    }   
    metadata def <problemStatement> ProblemStatementMetadata :> Metaobjects::SemanticMetadata {
        :>> baseType = problemStatements meta SysML::RequirementUsage;
    }   


}
