package Towel42Model {
    doc /* Minimal Viable SYSMOD Model Template */
    occurrence def Towel42Project {
        doc /* The project occurrence definition is the root element of the modeling project and provides the context including cross relationships. */
        requirement problemStatement4Towel42 {
            doc /* Problem Statement: How can we reliably prevent a traveler from leaving home without a towel by sensing departure intent and towel presence? */
        }
        part baseContextTowel42 {
            part user;
            part baseTowel42 {
                doc /* System idea: We provide TowelAlert: a tiny tag on the towel, a door/zone beacon, and a phone/watch app that detect when the user is about to step out without the tagged towel. */
                part tag;
                part beacon;
                part app;
            }
            connection alert connect user to baseTowel42;
        }
        part hitchhiker {
            doc /* Stakeholder: Interstellar traveler who must never set off without a towel. */
        }
        part systemContextTowel42 :> baseContextTowel42 {
            doc /* System Context in the problem space (part of the requirement specification) */
            part systemTowel42 :>> baseTowel42 {
                doc /* System in the problem space */
                port userPort : TowelAlert_PortDef::UserPort;
                state towelStates {
                    entry;
                    then idle;
                    state idle {
                        do action watchForDeparture ::> watchForDeparture;
                    }
                }
                action watchForDeparture { out item status : TowelAlert_Domain::TowelStatus; }
            }
            part user :> hitchhiker :>> user {
                doc /* Actor: Interstellar traveler */
                port userPort : ~TowelAlert_PortDef::UserPort;
            }
            interface towelReminder {
                end port user ::> user.userPort;
                end port towel ::> systemTowel42.userPort;
            }
            use case grabTowel {
                subject theSubject = systemTowel42;
                actor userActor = user;
                objective {
                    doc /* User wants to get out; system ensures that the towel comes along. */
                    satisfy requirementSpecification.alwaysBringTowel {
                        subject;
                    }
                }
                first start then recognizeStepOutside;
                first recognizeStepOutside then done;
                perform action recognizeStepOutside ::> systemTowel42.watchForDeparture;
            }
        }
        requirement requirementSpecification {
            doc /* List of system requirements */
            subject theSubject :> systemContextTowel42.systemTowel42;
            requirement <F001> alwaysBringTowel {
                subject theSubject = systemContextTowel42.systemTowel42;
                stakeholder hitchhiker;
                doc /* If the user is > 5 m away from the base and no towel is detected, an alarm must be triggered. */
            }
            requirement <NF001> alertPerformance {
                subject theSubject = systemContextTowel42.systemTowel42;
                stakeholder hitchhiker;
                doc /* An alarm must be triggered within 1 s. */
            }
        }
        part <towel42AlertContext> physicalArchitectureContextTowel42Alert :> systemContextTowel42 {
            doc /* Context of the physical solution architecture */
            part <towel42Alert> physicalArchitectureTowel42Alert :>> systemTowel42 {
                doc /* Physical Architecture of the solution system. */
            }
        }
        satisfy requirementSpecification by towel42AlertContext.towel42Alert;
    }
    package TowelAlert_PortDef {
        port def UserPort;
    }
    package TowelAlert_Domain {
        item def TowelStatus {
            attribute present : ScalarValues::Boolean;
        }
    }
}
