package SYSMOD_Zigzag_Pattern {
    package SolutionLevel0 {
        part def MySystemBaseArchitectureContext {
            part systemOfInterest : MySystemBaseArchitecture;
        }
        part def MySystemBaseArchitecture;
    }

    package ProjectLevel1 {
        part def MySystemProject {
            part baseContext : SolutionLevel0::MySystemBaseArchitectureContext;
            requirement systemRequirements : ProblemLevel1::MySystemRequirements {
                subject :>> theSystem = baseContext.systemOfInterest;
            }
            part systemContext : ProblemLevel1::MySystemContext;
            part systemArchitectureContext : SolutionLevel1::MySystemPhysicalArchitectureContext;
        }
    }

    package ProblemLevel1 {
        requirement def MySystemRequirements {
            subject theSystem : SolutionLevel0::MySystemBaseArchitecture;
            requirement <REQ1> requirement1;
            requirement <REQ2> requirement2;
            requirement policyRequirements : PolicyRequirements::PolicyRequirements {
                doc /* 'require' does not work because there are no requirement usages */
            }
        }

        part def MySystemContext :> SolutionLevel0::MySystemBaseArchitectureContext {
            doc /* The system context specializes the base architecture context 
                * and adds additional elements required for the system problem space */        
            part :>> systemOfInterest : MySystem;
        }
        part def MySystem :> SolutionLevel0::MySystemBaseArchitecture;
    }

    package SolutionLevel1 {
        part def MySystemPhysicalArchitectureContext :> ProblemLevel1::MySystemContext {
            part :>> systemOfInterest : MySystemPhysicalArchitecture;
        }
        part def MySystemPhysicalArchitecture :> ProblemLevel1::MySystem {
            part component1 : Component1;
            part component2 : Component2;
        }
        part def Component1;
        part def Component2;
    }

    package ProblemLevel2 {
        requirement def MyComponentRequirements {
            subject theSubject : SolutionLevel1::Component1;
            requirement <REQ21> requirement21;
            requirement <REQ22> requirement22;
        }
    }
}

library package PolicyRequirements {
    requirement def PolicyRequirements {
        requirement <PREQ1> policyRequirement1;
        requirement <PREQ2> policyRequirement2;
    }
}