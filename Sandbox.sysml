package MySystemModel {
    private import SYSMOD::**;

    part def MySystemContext :> SystemContext {
        part user :> actors;
    }

    #systemContext part def MySystemContext2;
}