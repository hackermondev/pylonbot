fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .format(true)
        .out_dir("./rust")
        .compile(
            &[
                "./proto/dispatch/v1/service.proto",
                "./proto/quotas/v1/service.proto",
                "./proto/tasks/v1/service.proto",
                "./proto/kv/v1/service.proto",
                "./proto/google/protobuf/empty.proto",
            ],
            &["./proto"],
        )?;
    Ok(())
}
