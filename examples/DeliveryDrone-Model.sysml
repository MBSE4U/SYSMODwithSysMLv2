package RemoteDeliveryDroneProject {
    public import SYSMOD::*;

    // --- Brownfield System ---

    part def LastMileLogisticsSystem;

    part def LastMileLogisticsBrownfieldContext :> SystemContext {
        part :>> soi : LastMileLogisticsSystem;
        part logisticsOperator :> actors;
        part recipient :> actors;
        part transportVehicle :> actors;
    }

    // --- Stakeholders ---

    part def RecipientStakeholder :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::high;
        attribute :>> effort = LevelKind::medium;
        attribute :>> categories = StakeholderCategoryKind::user;
    }

    part def LogisticsOperatorStakeholder :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::critical;
        attribute :>> effort = LevelKind::high;
        attribute :>> categories = StakeholderCategoryKind::requirementOwner;
    }

    part def RegulatoryAuthority :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::critical;
        attribute :>> effort = LevelKind::high;
        attribute :>> categories = StakeholderCategoryKind::requirementOwner;
    }

    part def DroneMaintenanceEngineer :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::medium;
        attribute :>> effort = LevelKind::medium;
        attribute :>> categories = StakeholderCategoryKind::expert;
    }

    part def UrbanAuthority :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::high;
        attribute :>> effort = LevelKind::high;
        attribute :>> categories = StakeholderCategoryKind::requirementOwner;
    }

    part def DepotManager :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::medium;
        attribute :>> effort = LevelKind::medium;
        attribute :>> categories = StakeholderCategoryKind::user;
    }

    // --- Project Owner ---

    part def LogisticsProjectOwner :> ExtendedStakeholder {
        attribute :>> risk = LevelKind::critical;
        attribute :>> effort = LevelKind::low;
        attribute :>> categories = StakeholderCategoryKind::requirementOwner;
    }

    // --- Project ---

    occurrence def <project> RemoteDeliveryDroneProject :> Project {
        part :>> brownfieldContext : LastMileLogisticsBrownfieldContext;

        part :>> projectOwner : LogisticsProjectOwner;

        part recipient :> projectStakeholders : RecipientStakeholder;
        part logisticsOperator :> projectStakeholders : LogisticsOperatorStakeholder;
        part regulatoryAuthority :> projectStakeholders : RegulatoryAuthority;
        part droneMaintenanceEngineer :> projectStakeholders : DroneMaintenanceEngineer;
        part urbanAuthority :> projectStakeholders : UrbanAuthority;
        part depotManager :> projectStakeholders : DepotManager;

        concern :>> problemStatement {
            doc
            /* How can we transform last-mile goods delivery in urban and suburban
             * areas to be reliably on-time, cost-effective, and sustainable, while
             * working within the constraints of the existing logistics infrastructure?
             *
             * Today's last-mile logistics chain relies on a network of regional
             * distribution centers, sorting hubs, and fleets of delivery vehicles
             * operated by human drivers. Parcels are dispatched in batch runs,
             * assigned to drivers via static route plans, and handed off at the
             * recipient's door — or left undelivered when no one is home. This
             * system was designed for predictable volumes and cooperative customers;
             * it was not built for the demands of modern e-commerce, where order
             * volumes fluctuate wildly, delivery windows are expected within hours,
             * and each failed delivery attempt cascades into additional cost and
             * emissions.
             *
             * The brownfield system — dispatch software, vehicle fleets,
             * hub-and-spoke depot networks, and manual delivery workflows — imposes
             * hard constraints: routes are pre-planned, real-time rerouting is
             * limited, driver capacity is fixed, and failed-delivery handling is
             * manual and slow. As delivery density rises in urban cores and
             * customers demand ever-shorter windows, the gap between what the
             * existing system can deliver and what customers expect continues to
             * widen. The result is rising operational costs, increasing carbon
             * footprint, a growing number of failed deliveries, and declining
             * customer satisfaction.
             */
        }
    }
}
