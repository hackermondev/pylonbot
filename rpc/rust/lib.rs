pub mod kv {
    pub mod v1 {
        include!("rpc.kv.v1.rs");
    }
}

pub mod dispatch {
    pub mod v1 {
        include!("rpc.dispatch.v1.rs");
    }
}

pub mod quotas {
    pub mod v1 {
        include!("rpc.quotas.v1.rs");
    }
}

pub mod tasks {
    pub mod v1 {
        include!("rpc.tasks.v1.rs");
    }
}

pub mod common {
    pub mod v1 {
        include!("rpc.common.v1.rs");
    }
}
