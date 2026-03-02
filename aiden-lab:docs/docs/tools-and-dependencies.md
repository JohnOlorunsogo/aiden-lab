---
sidebar_position: 2
---

# Aiden Lab Architecture: Tools and Dependencies

This page documents every tool, runtime, and platform component that makes up the Aiden Lab environment — from the bare-metal host to the guest OS running inside the virtual machine.

---

## Section 1: Infrastructure & Virtualization Platform

This section covers the core layers that provision, orchestrate, and run virtual machines in the Aiden Lab environment.

### Host Infrastructure & Runtimes

#### OpenEuler

**Role:** Bare-metal Host Operating System

OpenEuler is the Linux distribution running directly on the physical server. It provides:

- The OS kernel and hardware abstraction layer
- Access to physical CPU, RAM, storage, and NICs
- KVM kernel modules that enable hardware-accelerated virtualization
- The base system for running Kubernetes, Containerd, and Docker

All other components — Kubernetes, KubeVirt, and the VMs themselves — run on top of OpenEuler.

#### Containerd

**Role:** Container Runtime Interface (CRI) for Kubernetes

Containerd is the primary container runtime that Kubernetes uses to pull and run container images. In the Aiden Lab stack:

- It runs the underlying pods that Kubernetes schedules (including KubeVirt's `virt-launcher` pod)
- It caches the `aiden_labs` container image in the `k8s.io` namespace
- It handles image layer management and container lifecycle

```bash
# Verify the aiden_labs image is cached in containerd
crictl images | grep aiden_labs
# or using ctr
ctr -n k8s.io images list | grep aiden_labs
```

#### Docker Engine

**Role:** Image Build & Registry Push Tool

Docker is used as the build-time toolchain, not at runtime. Its responsibilities are:

- Building the custom container image via `docker build` that packages the `.qcow2` virtual disk file
- Pushing the resulting image to Docker Hub for distribution
- Providing a convenient layer cache during iterative image development

```bash
# Build the container image containing the .qcow2 disk
docker build -t your-dockerhub-user/aiden_labs:latest .

# Push to Docker Hub so Kubernetes/Containerd can pull it
docker push your-dockerhub-user/aiden_labs:latest
```

---

### Orchestration & Networking

#### Kubernetes (K8s)

**Role:** Central Orchestration Engine

Kubernetes is the control plane that manages everything in the Aiden Lab environment. It:

- Schedules and places VM workloads (as pods) across nodes
- Manages compute resource allocation (CPU, memory requests/limits)
- Handles service discovery and NodePort routing for external access
- Runs the KubeVirt operator and all supporting controllers

Key components active in the cluster:

| Component | Description                                                   |
| --------- | ------------------------------------------------------------- |
| `kubeadm` | Used to bootstrap and configure the cluster                   |
| `kubelet` | Node agent that registers each node and manages pod lifecycle |
| `kubectl` | CLI for interacting with the Kubernetes API                   |

#### Cilium

**Role:** Container Network Interface (CNI) Plugin

Cilium provides networking between pods, nodes, and external clients using **eBPF** technology. In the Aiden Lab setup:

- Routes packets between the host network, KubeVirt pods, and external clients
- Enforces network policies between namespaces
- Provides fast, kernel-level datapath without `iptables` overhead
- Enables secure, observable traffic flows to and from VMs

#### NodePort (Kubernetes Service)

**Role:** External Traffic Gateway

A Kubernetes `NodePort` service exposes each VM to the outside network. When a user connects via RDP:

1. The client connects to the host node IP on a high port (e.g., `10.1.1.164:30001`)
2. Kubernetes routes the traffic to the correct service
3. The service forwards it to the `virt-launcher` pod running the VM
4. The VM receives the connection on its internal port `3389` (RDP)

```yaml
# Example NodePort service for a VM
apiVersion: v1
kind: Service
metadata:
  name: windows-vm-rdp
spec:
  type: NodePort
  selector:
    vm.kubevirt.io/name: windows-vm
  ports:
    - port: 3389
      targetPort: 3389
      nodePort: 30001
```

---

### Virtualization Engine

#### KubeVirt

**Role:** Kubernetes Operator for VM Management

KubeVirt extends Kubernetes with custom resource definitions (CRDs) that allow VMs to be created, managed, and deleted using standard Kubernetes YAML manifests. In the Aiden Lab stack:

- It introduces the `VirtualMachine` and `VirtualMachineInstance` resource types
- It translates VM YAML specs into instructions for QEMU/KVM
- It manages the full VM lifecycle: start, stop, pause, resume, delete
- It runs a `virt-launcher` pod for each active VM instance

```bash
# Deploy a VM from a YAML manifest
kubectl apply -f windows-vm.yaml

# Check running VM instances
kubectl get vmi

# Delete a VM
kubectl delete vm windows-vm
```

#### QEMU / KVM

**Role:** Hypervisor Engine

QEMU and KVM are the actual hypervisor components that run inside the `virt-launcher` pod.

| Component | Role                                                                                                                             |
| --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **KVM**   | Linux kernel module that provides hardware-level CPU virtualization (Intel VT-x / AMD-V). Gives VMs near-native CPU performance. |
| **QEMU**  | User-space emulator that emulates hardware devices (disk controller, NIC, USB, display). Works with KVM to run the full VM.      |

Together, QEMU+KVM give the Windows 10 guest a complete virtual hardware environment while KubeVirt manages the pod wrapping it all.

---

## Section 2: Management Tools & Guest Environment

This section covers the CLI tools used to interact with the stack and the software environment running inside the virtual machines.

### Management & CLI Tools

#### kubectl

**Role:** Kubernetes Command-Line Interface

`kubectl` is the primary tool for managing the Kubernetes cluster and all VM resources. Common operations in Aiden Lab:

```bash
# Deploy a VM
kubectl apply -f windows-vm.yaml

# List running VM instances
kubectl get vmi

# Describe a specific VM instance (useful for debugging)
kubectl describe vmi windows-vm

# View logs from the virt-launcher pod
kubectl logs pod/<virt-launcher-pod-name>

# Delete a VM
kubectl delete vm windows-vm
```

#### virtctl

**Role:** KubeVirt-Specific CLI

`virtctl` is the companion CLI for KubeVirt, providing VM-specific operations that `kubectl` doesn't natively support:

```bash
# Open a VNC console to the VM (graphical access)
virtctl vnc windows-vm

# Stream serial console output (text-based logs)
virtctl console windows-vm

# Pause a running VM
virtctl pause vm windows-vm

# Resume a paused VM
virtctl unpause vm windows-vm

# Start / Stop
virtctl start windows-vm
virtctl stop windows-vm
```

#### crictl / ctr

**Role:** Low-Level Container Runtime Inspection Tools

These tools bypass Kubernetes and interact directly with the Containerd runtime. They are used to verify that image pulls have completed and inspect the container cache:

```bash
# List all images in containerd (crictl)
crictl images

# List images in the k8s.io namespace (ctr)
ctr -n k8s.io images list

# Verify the aiden_labs image is present
ctr -n k8s.io images list | grep aiden_labs

# Pull an image manually into containerd
ctr -n k8s.io images pull docker.io/your-user/aiden_labs:latest
```

---

### Guest Environment & Applications

#### Windows 10

**Role:** Guest Operating System

Windows 10 runs as the guest OS inside the virtual machine. It is stored as a `.qcow2` virtual hard disk image, which is:

- Packaged inside a container image during the `docker build` step
- Pulled by Containerd when the `VirtualMachineInstance` is scheduled
- Mounted by QEMU as the VM's primary boot disk

The `.qcow2` format supports copy-on-write, allowing the base image to be shared while each VM instance writes its own changes to a separate overlay.

#### ENSP (Enterprise Network Simulation Platform)

**Role:** Huawei Network Simulation Software

ENSP is Huawei's enterprise network simulation platform, pre-installed inside the Windows 10 guest. It enables:

- Running virtual Huawei routers, switches, and firewalls
- Designing and testing network topologies
- Simulating routing protocols (OSPF, BGP, IS-IS), VLANs, and ACLs

ENSP is the primary application that Aiden Lab users interact with through the remote desktop session. The AIDEN Logger system captures eNSP console output for AI-powered error analysis.

#### RDP (Remote Desktop Protocol)

**Role:** User Access Protocol

RDP (port `3389`) is the protocol used to remotely access the Windows 10 desktop from a client machine. In the Aiden Lab flow:

1. A user connects to `<node-ip>:<nodeport>` (e.g., `10.1.1.164:30001`) using any RDP client
2. Kubernetes routes the traffic through the NodePort service to the `virt-launcher` pod
3. The Windows 10 guest accepts the connection on port `3389`
4. The user gets a full graphical desktop session with ENSP available

```
Client → 10.1.1.164:30001 → NodePort Service → virt-launcher pod → Windows 10 :3389
```

RDP provides the full desktop experience needed to launch ENSP, configure network topologies, and observe router console output in real time.
