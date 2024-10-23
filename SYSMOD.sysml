library package SYSMOD {
    doc
    /*
     * Definition of SYSMOD Concepts
     *
     * Copyright 2014, MBSE4U
     */

    part def Stakeholder {
        doc
        /*
         * SYSMOD-specific definition of the stakeholder concept
         */
        attribute risk : PriorityKind;
        attribute effort : PriorityKind;
        attribute context : ScalarValues::String;
    }

    alias PriorityKind for RiskMetadata::LevelEnum;

    requirement def ProblemStatement {
        assert constraint {
            not (subj istype Base::Anything) and
            SequenceFunctions::size(stakeholders) > 0 
        }
    }
}
