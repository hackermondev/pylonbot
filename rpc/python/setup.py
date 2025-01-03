import os

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py


class build_proto(build_py):
    def run(self):
        cwd = os.getcwd()
        os.chdir("..")

        # Gather proto files
        protos = []
        for root, dirs, files in os.walk("proto"):
            if "google" in root:
                continue

            for name in files:
                if name.endswith(".proto") and not name.startswith("_"):
                    protos.append(os.path.join(root, name))

        # Build protos
        os.system(
            f"python3 -m grpc_tools.protoc -I./proto --python_betterproto_out=python/ {' '.join(protos)}"
        )

        # Reset chdir
        os.chdir(cwd)

        return super().run()


setup(
    name="rpc",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["protobuf==3.11.3"],
    cmdclass={"build_proto": build_proto},
)
