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


package <FFDS_MODEL> ForestFireObservationSystemModel {
    doc /* SysML v2 SYSMOD Example of a Forest Fire Observation System
         * 
         * The purpose of this example is demonstrating the application of SYSMOD using SysML v2
         * 
         * Copyright 2024, MBSE4U
         */

    comment ShortNamesNamingConventions
    /* 
     * BA       -   Base Architecture
     * BC       -   Base Context
     * LA       -   Logical Architecture
     * PA       -   Physical Architecture
     * PC       -   Product Context
     * PRJ      -   Project
     * SC       -   System Context
     * SYS      -   System Namespace
     * UC       -   Use Case
    */

    part def <FFDS_PC> ForestFireObservationProjectContext :> SYSMOD::ProjectContext {
        doc /* 
             * Definition of the project context of the Forest Fire Observation System. 
             */

        part <ffds> forestFireDetectionSystem : ForestFireDetectionSystem :> systemOfInterest;
        part forests[*] : Forest :> actors {
            doc /* All forests to be monitored by the forest fire detection system. */
        }
        connection ffdsForestsConnection :> systemActorConnection connect forests to ffds  {
            doc /* Abstract connection between the forests and the forest fire detection system. */
            assert constraint {
                QuantityCalculations::sum(forests.area) <= ffds.maxForestAreaCovered
            }
        }

        requirement problemStatement :> problemStatement {
            doc /*
                 * How can forest authorities monitor vast and diverse forest areas of at least 2500000 square kilometers
                 * efficiently, detect potential fires early to save lives, and minimize environmental damage, 
                 * contributing to long-term forest sustainability? As a company developing forest 
                 * fire detection systems, how can we design adaptable, scalable, and eco-friendly 
                 * solutions that cater to various forest types and sizes, ensuring reliability, 
                 * rapid response, and ease of integration for different stakeholders while promoting 
                 * sustainable forest management?
                 */
            subject ffds : ForestFireDetectionSystem;
            stakeholder :> ceoFFDS;
            stakeholder :> forestAuthority;
            require constraint {
                ffds.maxForestAreaCovered >= 2500000 [SI::'m²']
            }
        }
        satisfy problemStatement by ffds;            

        part forestAuthority :> stakeholders {
            doc /* 
                 * The Forest Authority is responsible for managing forest resources, 
                 * preserving biodiversity, monitoring forest health, and preventing and 
                 * mitigating forest fires. Their primary focus is to ensure public safety 
                 * and the sustainable use of forest areas. */
            attribute :>> risk = SYSMOD::PriorityKind::high;
            attribute :>> effort = SYSMOD::PriorityKind::medium;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Expert);
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
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::RequirementOwner);
        }
    }
    part <ffds_pc> forestFireDetectionSystemProductContext : FFDS_PC;

    part def <FFDS> ForestFireDetectionSystem {
        doc /* Entry point of the Project: Goal is to develop a Forest Fire Detection System */
        attribute maxForestAreaCovered :> ISQ::area {
           doc /* Maximum area that can be monitored by the FFDS. */
        }

        attribute minSizeOfFire :> ISQ::area {
            doc /* Minimum size of fire that is detected by the system. */
        }

        attribute timeFromDetectionToNotification :> ISQ::duration {
           doc /* Time from Detecting a potential fire until notification. */
        }
    }

    part def Forest {
        doc /* Definition of the forests to be monitored. */
        attribute area :> ISQ::area {
            doc /* Area of the forest. */
        }
    }

    package <BA> ForestFireDetectionSystemBaseArchitexture {
        part def <BC> ForestFireDetectionSystemBaseContext {
            doc /* Definition of the Base System Context of the Forest Fire Detection System */
                part <ffds> forestFireDetectionSystem : FFDS :> FFDS_MODEL::ffds_pc.ffds;
                part <env> environment : Actors::Environment;
                interface env.fire.firePort to ffds.fireDetectionPort;                
        }
        part def <FFDS> ForestFireDetectionSystem {
            use case detectAndReportFire : UC::DetectandReportFire;
            port fireDetectionPort;
            port fireAlertPort;
        }

        package Actors {
            part def Fire {
                port firePort;
            }
        }

        package <UC> UseCases {
            use case def DetectandReportFire {
                subject ffds : ForestFireDetectionSystem;
                in item fireSignature[*];
                out item fireAlert;
            }
        }
    }
 
    package <UC> ForestFireDetectionSystemUseCases {
        use case <observeArea> 'observe area by drone'; // model relationship to ffds behavior
    }

    package <SARCH> ForestFireDetectionSystemSystemArchitecture {
        part def <FFDS> ForestFireDetectionSystem {
        }
    }
}
