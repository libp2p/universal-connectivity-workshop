use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use fs_err as fs;
use std::path::Path;
use std::process::Command;
use toml::Value;

#[derive(Debug, Parser)]
#[command(name = "xtask")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Build all workspace members and their Docker images
    Build,
    /// Publish all Docker images to the registry
    Publish,
}

fn main() -> Result<()> {
    // Parse command line arguments
    let cli = Cli::parse();
    match &cli.command {
        Commands::Build => build_all(),
        Commands::Publish => build_all().and_then(|_| publish_all()),
    }
}

fn get_workspace_members() -> Result<Vec<String>> {
    let cargo_toml = fs::read_to_string("Cargo.toml").context("Failed to read Cargo.toml")?;
    let parsed: Value = toml::from_str(&cargo_toml).context("Failed to parse Cargo.toml")?;

    let members = parsed
        .get("workspace")
        .and_then(|w| w.get("members"))
        .and_then(|m| m.as_array())
        .context("No workspace members found in Cargo.toml")?;

    let mut member_paths = Vec::new();
    for member in members {
        if let Some(path) = member.as_str()
            && path != "xtask"
        {
            member_paths.push(path.to_string());
        }
    }

    Ok(member_paths)
}

fn get_image_name_from_path(member_path: &str) -> String {
    let path = Path::new(member_path);
    let parent_dir = path
        .parent()
        .and_then(|p| p.file_name())
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");
    format!("ucw-checker-{parent_dir}")
}

fn build_all() -> Result<()> {
    let member_paths = get_workspace_members()?;

    for member_path in &member_paths {
        println!("Building workspace member: {member_path}");

        // Build the Rust application
        let status = Command::new("cargo")
            .args(["build"])
            .current_dir(member_path)
            .status()
            .context(format!("Failed to build member at {member_path}"))?;
        if !status.success() {
            anyhow::bail!("Build failed for member at {member_path}");
        }

        // Build Docker image
        let image_name = get_image_name_from_path(member_path);
        let full_image_name =
            format!("ghcr.io/libp2p/universal-connectivity-workshop/{image_name}:latest");

        println!("Building Docker image: {full_image_name}");
        let status = Command::new("docker")
            .args(["build", "-t", &full_image_name, "."])
            .current_dir(member_path)
            .status()
            .context(format!("Failed to build Docker image for {member_path}"))?;
        if !status.success() {
            anyhow::bail!("Docker build failed for {member_path}");
        }
    }

    Ok(())
}

fn publish_all() -> Result<()> {
    let member_paths = get_workspace_members()?;

    for member_path in &member_paths {
        let image_name = get_image_name_from_path(member_path);
        let full_image_name =
            format!("ghcr.io/libp2p/universal-connectivity-workshop/{image_name}:latest");

        println!("Publishing Docker image: {full_image_name}");
        let status = Command::new("docker")
            .args(["push", &full_image_name])
            .current_dir(member_path)
            .status()
            .context(format!("Failed to push Docker image for {member_path}"))?;
        if !status.success() {
            anyhow::bail!("Docker push failed for {member_path}");
        }
    }

    Ok(())
}
