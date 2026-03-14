import subprocess
import sys


def run_step(script_name):
    print(f"\n===== Running {script_name} =====\n")

    result = subprocess.run(
        ["python", f"pipelines/{script_name}"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    if result.returncode != 0:
        print(f"\n XX Error while running {script_name}")
        sys.exit(1)

    print(f"\n--> Finished {script_name}")


def main():

    print("\nStarting Airport INR Data Pipeline\n")

    run_step("extract_buildings.py")

    run_step("build_mesh.py")

    run_step("generate_sdf_dataset.py")

    print("\n---> Pipeline completed successfully\n")


if __name__ == "__main__":
    main()