package <FFDS> ForestFireObservationSystem {
    doc /* SysML v2 SYSMOD Example of a Forest Fire Observation System
         * 
         * The purpose of this example is demonstrating the application of SYSMOD using SysML v2
         * 
         * Copyright 2014, MBSE4U
         */

    comment ShortNamesNamingConventions
    /* */

    package <PROJECT> ForestFireObservationSystemProject {
        
        part def <FFDS_PC> ForestFireObservationProductContext {
            doc /* Definition of the project context of the Forest Fire Observation System. 
                 * It includes besides others the stakeholders, their concerns, the problem statement 
                 * and the base architecture including the context. 
                 */

            part def ForestFireDetectionSystem {
                doc /* Entry point of the Project: Goal is to develop a Forest Fire Detection System */

                attribute maxForestAreaCovered :> ISQ::area;
            }

            requirement problemStatement : SYSMOD::ProblemStatement {
                doc /* The problem statement of the Forest Fire Detection System. */
                subject ffds : ForestFireDetectionSystem;
                stakeholder :> ceoFFDS;
                stakeholder :> forestAuthority;
                require constraint {
                    doc /*
                         * How can forest authorities monitor vast and diverse forest areas of at least 2500000 square kilometers
                         * efficiently, detect potential fires early to save lives, and minimize environmental damage, 
                         * contributing to long-term forest sustainability? As a company developing forest 
                         * fire detection systems, how can we design adaptable, scalable, and eco-friendly 
                         * solutions that cater to various forest types and sizes, ensuring reliability, 
                         * rapid response, and ease of integration for different stakeholders while promoting 
                         * sustainable forest management?
                         */
                    ffds.maxForestAreaCovered >= 2500000 [SI::'m²']
                }
            }

            part stakeholders [*] : SYSMOD::Stakeholder;
            part forestAuthority :> stakeholders {
                doc /* 
                     * The Forest Authority is responsible for managing forest resources, 
                     * preserving biodiversity, monitoring forest health, and preventing and 
                     * mitigating forest fires. Their primary focus is to ensure public safety 
                     * and the sustainable use of forest areas. */
                attribute :>> risk = SYSMOD::PriorityKind::high;
                attribute :>> effort = SYSMOD::PriorityKind::medium;
            }
            part ceoFFDS :> stakeholders {
                doc /* 
                     * The CEO oversees the development, commercialization, and strategic growth 
                     * of the company that specializes in forest fire detection systems. Their primary 
                     * focus is ensuring the company's products are innovative, reliable, and meet market 
                     * demands while maintaining profitability and corporate responsibility.
                    */
                attribute :>> risk = SYSMOD::PriorityKind::high;
                attribute :>> effort = SYSMOD::PriorityKind::medium;
            }            
        }

        part def <C> ForestFireDetectionSystemBaseContext {
            doc /* Definition of the Base System Context of the Forest Fire Detection System */
                part <ffds> forestFireDetectionSystem : FFDS;
        }

        part def <FFDS> ForestFireDetectionSystem {
            action observeArea {
                first start;
                then action defineObservationArea;
                then action approachArea;
                then action flyObservationPatterns;
                then action returnToBaseStation;
                then done;
            }
        }
    }
 
    package <SUC> ForestFireDetectionSystemUseCases {

        private import PROJECT::C::ffds;

        use case <observeArea> 'observe area by drone'; // model relationship to ffds behavior
    }

    package <SARCH> ForestFireDetectionSystemSystemArchitecture {
        part def <FFDS> ForestFireDetectionSystem :> PROJECT::FFDS {
        }
    }
}
