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

package <FFDS_MODEL> ForestFireDetectionSystemModel {
    doc /* SysML v2 SYSMOD Example of a Forest Fire Detection System
         * 
         * The purpose of this example is demonstrating the application of SYSMOD using SysML v2
         * 
         * Version 1.0beta 
         *
         * Copyright 2024, MBSE4U
         */

    comment ShortNamesNamingConventions
    /* 
     * BA       -   Base Architecture
     * BC       -   Base Context
     * LA       -   Logical Architecture
     * PA       -   Physical Architecture
     * PC       -   Project Context
     * PKG      -   Package
     * PRJ      -   Project
     * SA       -   System Architecture
     * SC       -   System Context
     * SYS      -   System Namespace
     * UC       -   Use Case
    */

    private import SYSMOD_Metadata::*;

    occurrence def <FFDS_PC> ForestFireObservationProject :> SYSMOD::Project {
        doc /* 
             * Definition of the project context of the Forest Fire Observation System. 
             */

        // 
        // Problem Statement of the System
        //
        requirement :>> problemStatement  {
            doc /*
                 * How can forest authorities effectively monitor extensive and ecologically diverse forest regions spanning at least 2,500,000 square kilometers? The solution should enable early fire detection to protect human lives, reduce environmental impact and support the long-term sustainability of forest ecosystems. 
                 */
            stakeholder theCEO = ceoFFDS;
            stakeholder theForestAuthority = forestAuthority;
            require constraint {
                ffds.maxForestAreaCovered >= 2500000 [SI::'m²']
            }
        }

        //
        // List of System Stakeholders
        //
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
        part forestAuthority :> stakeholders {
            doc /*
                * Forest authorities are responsible for managing and conserving forested areas.
                * Their focus includes ensuring sustainable forest management practices,
                * monitoring for potential threats, and implementing preventative measures to protect
                * forest ecosystems from fire and other hazards.
                */
            attribute :>> risk = SYSMOD::PriorityKind::high;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::RequirementOwner, 
                                        SYSMOD::StakeholderCategoryKind::User);
        }
        part environmentalAgency :> stakeholders {
            doc /*
                * Environmental agencies work to protect and sustain the natural environment.
                * They ensure that fire detection systems align with environmental regulations,
                * policies, and sustainability goals, providing guidelines and approvals.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::RequirementOwner, 
                                        SYSMOD::StakeholderCategoryKind::Expert);
        }
        part localCommunities :> stakeholders {
            doc /*
                * Local communities residing near or within forested areas are directly affected by
                * forest fires and rely on the system for early warnings to protect lives and property.
                * They advocate for system accessibility and user-friendly alert mechanisms.
                */
            attribute :>> risk = SYSMOD::PriorityKind::high;
            attribute :>> effort = SYSMOD::PriorityKind::medium;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::User, 
                                        SYSMOD::StakeholderCategoryKind::Other);
        }
        part emergencyResponseTeams :> stakeholders {
            doc /*
                * Emergency response teams, including firefighters and first responders, require
                * accurate and timely data from the detection system to respond quickly and
                * effectively to forest fire incidents.
                */
            attribute :>> risk = SYSMOD::PriorityKind::high;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::User, 
                                        SYSMOD::StakeholderCategoryKind::Expert);
        }
        part technologyProviders :> stakeholders {
            doc /*
                * Technology providers develop and supply essential hardware and software components
                * for the detection system. They are responsible for ensuring that the system
                * integrates new technology standards and remains adaptable and scalable.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Expert, 
                                        SYSMOD::StakeholderCategoryKind::Other);
        }
        part policyMakers :> stakeholders {
            doc /*
                * Policy makers influence regulations and guidelines for forest management and
                * fire prevention. They ensure that detection systems comply with national and
                * international laws and promote sustainable practices.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::RequirementOwner, 
                                        SYSMOD::StakeholderCategoryKind::Other);
        }
        part insuranceCompanies :> stakeholders {
            doc /*
                * Insurance companies are interested in the system's impact on reducing fire risks
                * and minimizing potential losses. They may support or invest in systems that lower
                * claim risks for properties within or near forested areas.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::medium;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Other);
        }
        part dataScientists :> stakeholders {
            doc /*
                * Data scientists analyze and interpret data collected by the system, developing
                * predictive models for early detection and prevention strategies.
                * Their insights contribute to refining system algorithms and improving detection accuracy.
                */
            attribute :>> risk = SYSMOD::PriorityKind::low;
            attribute :>> effort = SYSMOD::PriorityKind::high;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Expert);
        }
        part sustainabilityExperts :> stakeholders {
            doc /*
                * Sustainability experts ensure that the system aligns with environmental sustainability goals,
                * advocating for eco-friendly technologies and minimal environmental impact throughout the
                * system's life cycle.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::medium;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Expert);
        }
        part financialAnalysts :> stakeholders {
            doc /*
                * Financial analysts assess the economic viability of the detection system, focusing on costs,
                * return on investment, and long-term financial sustainability for the company and clients.
                */
            attribute :>> risk = SYSMOD::PriorityKind::medium;
            attribute :>> effort = SYSMOD::PriorityKind::medium;
            attribute :>> categories = (SYSMOD::StakeholderCategoryKind::Other);
        }        


        //
        // Base Architecture of the Forest Fire Detection System
        //
        part ffdsBaseContext : SYSMOD::SystemContext {
            part forest : FFDS_BA_PKG::Actors::Forest :> actors {
                doc /* Forest to be monitored by the forest fire detection system. */
            }
            connection ffdsForestsConnection connect forest to systemOfInterest  {
                doc /* Abstract connection between the forest and the forest fire detection system. */
                assert constraint {
                    QuantityCalculations::sum(forest.area) <= ffds.maxForestAreaCovered
                }
            }
        }
        part ffdsBaseArchitectureContext :> ffdsBaseContext {
            part <ffds> forestFireDetectionSystem : ForestFireDetectionSystem :>> systemOfInterest;
        }
    }

    part def <FFDS> ForestFireDetectionSystem {
        doc /* Entry point of the Project: Goal is to develop a Forest Fire Detection System */
        private import ParametersOfInterestMetadata::*;

        #moe attribute maxForestAreaCovered :> ISQ::area {
           doc /* Maximum area that can be monitored by the FFDS. */
        }
        #moe attribute minSizeOfFire :> ISQ::area {
            doc /* Minimum size of fire that is detected by the system. */
        }
        #moe attribute timeFromDetectionToNotification :> ISQ::duration {
           doc /* Time from Detecting a potential fire until notification. */
        }
    }

    package <FFDS_BA_PKG> ForestFireDetectionSystemBaseArchitexture {
        doc /* Base Architecture of the Forest Fire Detection System */
        
        part def <FFDS_BC> ForestFireDetectionSystemBaseContext : SYSMOD::SystemContext {
            doc /* Definition of the Base Architecture Context of the Forest Fire Detection System */
            
            // the system and the actors
            part <ffds> forestFireDetectionSystem : FFDS :> FFDS_MODEL::ffds_pc.ffds :>> systemOfInterest;
            part forest :> ffds_pc.forest;
            part fires[*] : Actors::Fire;
            part fireDepartments[*] : Actors::FireDepartment;
            part operators[*] : Actors::Operator;

            // the connections
            connect forest to ffds;
            interface fires.firePort to ffds.fireDetectionPort;
            interface fireDepartments.fireAlertPort to ffds.fireAlertPort;
            interface operators.operatorPort to ffds.operatorPort;
        }

        part def <FFDS> ForestFireDetectionSystem {
            doc SystemIdea /* */

            port fireDetectionPort;
            port fireAlertPort;
            port operatorPort;

            part observationStation;
            part satellites[*];
            connection obsStation2Satellites connect observationStation to satellites;

            part controlCenter;
            connection control2Satellites connect controlCenter to satellites;
            connection control2Observation connect controlCenter to observationStation;

            part sensorNetwork {
                part thermalSensors[*];
                part smokeDetectors[*];
                part humiditySensors[*];
                part windSensors[*];
                part animalSensors[*];
            }
            connection sensors2Observation connect sensorNetwork to observationStation;

            part dataProcessingUnit {
                part aiAlgorithm;
                part dataStorage;
            }
            connection control2DataProcessing connect controlCenter to dataProcessingUnit;

            part communicationNetwork {
                part wirelessTransmitters[*];
                part relayStations[*];
                part satelliteLink;
            }
            connection communication2Control connect communicationNetwork to controlCenter;
            connection communication2Sensors connect communicationNetwork to sensorNetwork;

            part userInterface {
                part operatorConsole;
                part mobileApp;
                part webPortal;
            }
            connection interface2Control connect userInterface to controlCenter;

            part powerSupplySystem {
                part solarPanels[*];
                part backupBattery[*];
            }
            connection power2Observation connect powerSupplySystem to observationStation;
            connection power2Sensors connect powerSupplySystem to sensorNetwork;

            part maintenanceSystem {
                part diagnosticTools;
                part alertManagement;
            }
            connection maintenance2Control connect maintenanceSystem to controlCenter;
            connection maintenance2Sensors connect maintenanceSystem to sensorNetwork;

            part weatherForecastIntegration;
            connection weather2DataProcessing connect weatherForecastIntegration to dataProcessingUnit;
        }


        package Actors {

            part def Fire {
                port firePort;
            }

            part def Forest {
                doc /* Definition of the forests to be monitored. */
                attribute area :> ISQ::area {
                    doc /* Area of the forest. */
                }
            }

            part def FireDepartment {
                port fireAlertPort;
            }

            part def Operator {
                port operatorPort;
            }
        }
    }
 
    package <FFDS_UC_PKG> ForestFireDetectionSystemUseCases {
        use case <detectandReportFire> 'detect and report fire' {
            subject ffds : FFDS_BA_PKG::ForestFireDetectionSystem;
            in item fireSignature[*];
            out item fireAlert;
        }
    }

    package <FFDS_RE_PKG> ForestFireDetectionSystemRequirements {

        package <FFDS_SC_PKG> ForestFireDetectionSystemContext {

            part def <FFDS_SC> ForestFireDetectionSystemContext :> FFDS_BA_PKG::ForestFireDetectionSystemBaseContext {
                part :>> ffds : FFDS_RE;
                satisfy FFDS_MODEL::ffds_pc.problemStatement by ffds;            
            }
            part def <FFDS_RE> ForestFireDetectionSystem :> FFDS_BA_PKG::ForestFireDetectionSystem;
        }
    }


    package <FFDS_SA_PKG> ForestFireDetectionSystemLogicalArchitecture {
        part def <FFDS> ForestFireDetectionSystem :> FFDS_BA_PKG::ForestFireDetectionSystem;

        alias ForestFireObservationDrone for ForestFireObservationDrone;
    }
}


package <DRONE_PL> DroneProductLineModel {

    package <DRONE_FM> DroneFeatureModel {

    }
    package <DRONE_SAS> DroneSharedAssetsSuperset {

        part def DroneSystem {
            part droneControlSystem {
                perform DRONE_SAS_UC::'observe area by drone'.defineObservationArea;
            }
            part drone;
            part charger;

            perform DRONE_SAS_UC::'observe area by drone'.approachArea;
            perform DRONE_SAS_UC::'observe area by drone'.flyObservationPatterns;
            perform DRONE_SAS_UC::'observe area by drone'.returnToBaseStation;
        }

        package <DRONE_SAS_UC> DroneSharedAssetsSupersetUseCases {
            use case <observeArea> 'observe area by drone' {
                first start;
                then action defineObservationArea;
                then action approachArea;
                then action flyObservationPatterns;
                then action returnToBaseStation;
                then done;
            }
        }
    }
}

package <FFOD_PKG> ForestFireObservationDrone {

    part def <FFOD> ForestFireObservationDroneSystem :> DRONE_PL::DRONE_SAS::DroneSystem;
}
