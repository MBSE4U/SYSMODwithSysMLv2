library package SYSMOD {
    doc
    /*
     * Definition of SYSMOD Concepts
     *
     * Copyright 2014, MBSE4U
     */

    part def ProjectContext :> SystemContext {
        doc /*
             * The Project Context includes the system problem statement and corresponding stakeholders,
             * the initial version of the system of interest and potential system actors.
             */
        requirement problemStatement : ProblemStatement;
        part stakeholders[*] : Stakeholder;
    }

    part def SystemContext {
        doc /*
             * The System Context includes all system actors, the system of interest, 
             * and the relationships between the actors and the system.
             */
        part actors[*];
        part systemOfInterest;
        connection systemActorConnection[*] connect actors to systemOfInterest;
    }

    part def Stakeholder {
        doc /*
             * SYSMOD-specific definition of the stakeholder concept
             */
        attribute risk : PriorityKind;
        attribute effort : PriorityKind;
        attribute contact : ScalarValues::String;
        attribute categories[*] : StakeholderCategoryKind;
    }
    alias PriorityKind for RiskMetadata::LevelEnum;
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
            not (subj istype Base::Anything) and
            SequenceFunctions::size(stakeholders) > 0 
        }
    }
}
