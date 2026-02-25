const API_BASE = 'http://localhost:8000';

const mockVMs = [
  {
    id: 'vm-001',
    name: 'win-vm-1',
    status: 'Running',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '10.244.1.15',
    externalIP: '34.234.56.78',
    rdpPort: 3389,
    uptime: '2h 15m',
    createdAt: '2026-02-24T10:00:00Z'
  },
  {
    id: 'vm-002',
    name: 'win-vm-2',
    status: 'Running',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '10.244.1.16',
    externalIP: '34.234.56.79',
    rdpPort: 3390,
    uptime: '1h 45m',
    createdAt: '2026-02-24T10:30:00Z'
  },
  {
    id: 'vm-003',
    name: 'win-vm-3',
    status: 'Stopped',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '10.244.1.17',
    externalIP: '34.234.56.80',
    rdpPort: 3391,
    uptime: '0m',
    createdAt: '2026-02-24T09:00:00Z'
  },
  {
    id: 'vm-004',
    name: 'dev-vm-1',
    status: 'Provisioning',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '',
    externalIP: '',
    rdpPort: 3392,
    uptime: '0m',
    createdAt: '2026-02-24T12:00:00Z'
  },
  {
    id: 'vm-005',
    name: 'test-vm-1',
    status: 'Running',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '10.244.1.18',
    externalIP: '34.234.56.81',
    rdpPort: 3393,
    uptime: '5h 30m',
    createdAt: '2026-02-24T06:30:00Z'
  },
  {
    id: 'vm-006',
    name: 'prod-vm-1',
    status: 'Running',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    internalIP: '10.244.1.19',
    externalIP: '34.234.56.82',
    rdpPort: 3394,
    uptime: '12h 45m',
    createdAt: '2026-02-23T22:15:00Z'
  }
];

let vmList = [...mockVMs];
let nextId = 7;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function fetchVMs() {
  await delay(300);
  return [...vmList];
}

export async function fetchVM(id) {
  await delay(200);
  const vm = vmList.find(v => v.id === id);
  if (!vm) throw new Error('VM not found');
  return { ...vm };
}

export async function createVM(vmData) {
  await delay(500);
  const newVM = {
    id: `vm-${String(nextId++).padStart(3, '0')}`,
    name: vmData.name,
    status: 'Provisioning',
    cpu: vmData.cpu,
    memory: vmData.memory,
    image: vmData.image || 'aiden_10-base:v1',
    internalIP: '',
    externalIP: '',
    rdpPort: 3389 + nextId,
    uptime: '0m',
    createdAt: new Date().toISOString()
  };
  vmList.push(newVM);
  
  setTimeout(() => {
    const idx = vmList.findIndex(v => v.id === newVM.id);
    if (idx >= 0) {
      vmList[idx].status = 'Running';
      vmList[idx].internalIP = `10.244.1.${20 + nextId}`;
      vmList[idx].externalIP = `34.234.56.${80 + nextId}`;
      vmList[idx].uptime = '0m';
    }
  }, 3000);
  
  return { ...newVM };
}

export async function createBulkVMs(count, baseName, cpu, memory, image) {
  await delay(800);
  const created = [];
  for (let i = 0; i < count; i++) {
    const newVM = {
      id: `vm-${String(nextId++).padStart(3, '0')}`,
      name: `${baseName}-${i + 1}`,
      status: 'Provisioning',
      cpu: cpu,
      memory: memory,
      image: image || 'aiden_10-base:v1',
      internalIP: '',
      externalIP: '',
      rdpPort: 3389 + nextId,
      uptime: '0m',
      createdAt: new Date().toISOString()
    };
    vmList.push(newVM);
    created.push({ ...newVM });
  }
  return created;
}

export async function deleteVM(id) {
  await delay(300);
  const idx = vmList.findIndex(v => v.id === id);
  if (idx < 0) throw new Error('VM not found');
  vmList.splice(idx, 1);
  return { success: true };
}

export async function deleteVMs(ids) {
  await delay(400);
  vmList = vmList.filter(v => !ids.includes(v.id));
  return { success: true, deleted: ids.length };
}
