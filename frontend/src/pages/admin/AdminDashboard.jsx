import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Trash2, 
  Eye,
  Server,
  Zap,
  Pause,
  Activity,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Cpu,
  HardDrive,
  Clock,
  Copy
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { StatsCard } from '@/components/ui/stats-card';
import { StatusBadge } from '@/components/ui/status-badge';
import { Separator } from '@/components/ui/separator';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter 
} from '@/components/ui/dialog';
import { fetchVMs, deleteVM, deleteVMs } from '@/services/vmApi';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4 px-4 py-3">
        <Skeleton className="h-4 w-4" />
        {[...Array(8)].map((_, i) => (
          <Skeleton key={i} className="h-4 w-24 flex-1" />
        ))}
      </div>
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-4">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-32 flex-1" />
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
          <div className="flex gap-1">
            <Skeleton className="h-8 w-8" />
            <Skeleton className="h-8 w-8" />
          </div>
        </div>
      ))}
    </div>
  );
}

function VMCard({ vm, index, isSelected, onSelect, onDelete, onView }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-[#020725]/40 border border-[#bdccd4]/10 rounded-xl p-4 hover:border-[#bdccd4]/20 transition-colors"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <Checkbox 
            checked={isSelected}
            onCheckedChange={(checked) => onSelect(vm.id, checked)}
          />
          <div>
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-[#bdccd4]/40" />
              <span className="text-[#bdccd4] font-medium">{vm.name}</span>
            </div>
            <StatusBadge status={vm.status} className="mt-1" />
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-[#bdccd4]/60 hover:text-[#24ab94] hover:bg-[#24ab94]/10"
            onClick={() => onView(vm.id)}
          >
            <Eye className="w-4 h-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-[#bdccd4]/60 hover:text-red-400 hover:bg-red-500/10"
            onClick={() => onDelete(vm)}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex items-center gap-2 text-[#bdccd4]/60">
          <Cpu className="w-3 h-3" />
          <span>{vm.cpu} cores</span>
        </div>
        <div className="flex items-center gap-2 text-[#bdccd4]/60">
          <HardDrive className="w-3 h-3" />
          <span>{vm.memory} Gi</span>
        </div>
        <div className="flex items-center gap-2 text-[#bdccd4]/60 col-span-2">
          <span className="font-mono text-xs">{vm.image}</span>
        </div>
        {vm.internalIP && (
          <div className="flex items-center gap-2 text-[#bdccd4]/60">
            <span className="text-xs">Internal:</span>
            <span className="font-mono text-xs">{vm.internalIP}</span>
          </div>
        )}
        {vm.externalIP && (
          <div className="flex items-center gap-2 text-[#bdccd4]/60">
            <span className="text-xs">External:</span>
            <span className="font-mono text-xs">{vm.externalIP}</span>
          </div>
        )}
        <div className="flex items-center gap-2 text-[#bdccd4]/60 col-span-2">
          <Clock className="w-3 h-3" />
          <span>{vm.uptime}</span>
        </div>
      </div>
    </motion.div>
  );
}

export default function AdminDashboard() {
  const [vms, setVms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVMs, setSelectedVMs] = useState([]);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [vmToDelete, setVmToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [hoveredRow, setHoveredRow] = useState(null);
  const navigate = useNavigate();

  const loadVMs = () => {
    fetchVMs()
      .then(data => {
        setVms(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        toast.error('Failed to load VMs');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadVMs();
  }, []);

  const stats = {
    total: vms.length,
    running: vms.filter(v => v.status === 'Running').length,
    stopped: vms.filter(v => v.status === 'Stopped').length,
    provisioning: vms.filter(v => v.status === 'Provisioning').length,
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedVMs(vms.map(v => v.id));
    } else {
      setSelectedVMs([]);
    }
  };

  const handleSelectVM = (vmId, checked) => {
    if (checked) {
      setSelectedVMs(prev => [...prev, vmId]);
    } else {
      setSelectedVMs(prev => prev.filter(id => id !== vmId));
    }
  };

  const handleDeleteSingle = (vm) => {
    setVmToDelete(vm);
    setDeleteDialogOpen(true);
  };

  const handleDeleteSelected = () => {
    if (selectedVMs.length === 0) return;
    setVmToDelete({ id: 'bulk', name: `${selectedVMs.length} VMs` });
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      if (vmToDelete.id === 'bulk') {
        await deleteVMs(selectedVMs);
        toast.success(`Deleted ${selectedVMs.length} VMs successfully`);
        setSelectedVMs([]);
      } else {
        await deleteVM(vmToDelete.id);
        toast.success(`Deleted ${vmToDelete.name} successfully`);
        setSelectedVMs(prev => prev.filter(id => id !== vmToDelete.id));
      }
      loadVMs();
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete VM(s)');
    } finally {
      setDeleting(false);
      setDeleteDialogOpen(false);
      setVmToDelete(null);
    }
  };

  const handleCopyIP = (ip) => {
    navigator.clipboard.writeText(ip);
    toast.success('IP address copied to clipboard');
  };

  const handleViewVM = (id) => {
    navigate(`/admin/vms/${id}`);
  };

  const allSelected = vms.length > 0 && selectedVMs.length === vms.length;
  const someSelected = selectedVMs.length > 0 && selectedVMs.length < vms.length;

  return (
    <div>
       {/* Hero Section */}
      <div className="relative -mx-4 md:-mx-8 mb-8 px-4 md:px-8 pt-6 md:pt-8 pb-10 overflow-hidden">
        <div 
          className="absolute inset-0 bg-[#020725]"
          style={{
            backgroundImage: `url('/Aiden lab Assets (Png & SVG)/Patterns/Asset 18.svg')`,
            backgroundSize: '600px',
            backgroundPosition: 'center',
            opacity: 0.15
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#020725]/50 to-[#020725]" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#24ab94]/5 via-transparent to-[#24ab94]/5" />
        
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <motion.h1 
              className="text-2xl md:text-3xl font-bold text-[#bdccd4] mb-2 font-notch"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              VM Management
            </motion.h1>
            <motion.p 
              className="text-[#bdccd4]/50 text-sm"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              Manage your virtual machines across the infrastructure
            </motion.p>
          </div>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Button 
              onClick={() => navigate('/admin/vms/new')}
              className="bg-[#24ab94] hover:bg-[#24ab94]/90 text-black font-medium gap-2 w-full sm:w-auto"
            >
              <Plus className="w-4 h-4" />
              Create VM
            </Button>
          </motion.div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-8">
        <StatsCard
          title="Total VMs"
          value={stats.total}
          icon={Server}
          color="teal"
        />
        <StatsCard
          title="Running"
          value={stats.running}
          icon={Activity}
          color="teal"
        />
        <StatsCard
          title="Stopped"
          value={stats.stopped}
          icon={Pause}
          color="slate"
        />
        <StatsCard
          title="Provisioning"
          value={stats.provisioning}
          icon={Zap}
          color="amber"
        />
      </div>

      {/* VM List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#020725]/30 border-[#bdccd4]/10 backdrop-blur-sm overflow-hidden">
          <CardContent className="p-0">
            <AnimatePresence>
              {selectedVMs.length > 0 && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="flex items-center gap-4 px-4 md:px-6 py-3 bg-[#24ab94]/10 border-b border-[#bdccd4]/10 overflow-hidden"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#24ab94]" />
                    <span className="text-sm text-[#bdccd4]">
                      {selectedVMs.length} selected
                    </span>
                  </div>
                  <Separator orientation="vertical" className="h-4 bg-[#bdccd4]/20 hidden sm:block" />
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={handleDeleteSelected}
                    className="text-red-400 hover:text-red-400 hover:bg-red-500/10 gap-1"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span className="hidden sm:inline">Delete Selected</span>
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto">
              {loading ? (
                <TableSkeleton />
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 z-10">
                    <tr className="border-b border-[#bdccd4]/10 bg-[#020725]/80 backdrop-blur-md">
                      <th className="text-left p-4 w-12">
                        <Checkbox 
                          checked={allSelected}
                          data-state={someSelected ? 'indeterminate' : allSelected ? 'checked' : 'unchecked'}
                          onCheckedChange={handleSelectAll}
                        />
                      </th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Name</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Status</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">CPU</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Memory</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Image</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Internal IP</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">External IP</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium">Uptime</th>
                      <th className="text-left p-4 text-xs uppercase tracking-wider text-[#bdccd4]/40 font-medium w-24">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vms.map((vm, index) => (
                      <motion.tr 
                        key={vm.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onMouseEnter={() => setHoveredRow(vm.id)}
                        onMouseLeave={() => setHoveredRow(null)}
                        className="border-b border-[#bdccd4]/5 transition-all duration-200 group relative"
                      >
                        <td 
                          className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#24ab94] transition-all duration-200"
                          style={{ opacity: hoveredRow === vm.id ? 1 : 0 }}
                        />
                        <td className="p-4 relative">
                          <Checkbox 
                            checked={selectedVMs.includes(vm.id)}
                            onCheckedChange={(checked) => handleSelectVM(vm.id, checked)}
                          />
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <Server className="w-4 h-4 text-[#bdccd4]/40" />
                            <span className="text-[#bdccd4] font-medium">{vm.name}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <StatusBadge status={vm.status} />
                        </td>
                        <td className="p-4 text-[#bdccd4]/70">{vm.cpu} cores</td>
                        <td className="p-4 text-[#bdccd4]/70">{vm.memory} Gi</td>
                        <td className="p-4 text-[#bdccd4]/70 font-mono text-xs">{vm.image}</td>
                        <td className="p-4">
                          {vm.internalIP ? (
                            <button
                              onClick={() => handleCopyIP(vm.internalIP)}
                              className="text-[#bdccd4]/70 font-mono text-xs hover:text-[#24ab94] transition-colors flex items-center gap-1"
                            >
                              {vm.internalIP}
                              <Copy className="w-3 h-3 opacity-50" />
                            </button>
                          ) : (
                            <span className="text-[#bdccd4]/30">-</span>
                          )}
                        </td>
                        <td className="p-4">
                          {vm.externalIP ? (
                            <button
                              onClick={() => handleCopyIP(vm.externalIP)}
                              className="text-[#bdccd4]/70 font-mono text-xs hover:text-[#24ab94] transition-colors flex items-center gap-1"
                            >
                              {vm.externalIP}
                              <Copy className="w-3 h-3 opacity-50" />
                            </button>
                          ) : (
                            <span className="text-[#bdccd4]/30">-</span>
                          )}
                        </td>
                        <td className="p-4 text-[#bdccd4]/70">{vm.uptime}</td>
                        <td className="p-4">
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8 text-[#bdccd4]/60 hover:text-[#24ab94] hover:bg-[#24ab94]/10"
                              onClick={() => handleViewVM(vm.id)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8 text-[#bdccd4]/60 hover:text-red-400 hover:bg-red-500/10"
                              onClick={() => handleDeleteSingle(vm)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden p-4 space-y-3">
              {loading ? (
                <>
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-40 bg-[#bdccd4]/5 rounded-xl animate-pulse" />
                  ))}
                </>
              ) : (
                vms.map((vm, index) => (
                  <VMCard
                    key={vm.id}
                    vm={vm}
                    index={index}
                    isSelected={selectedVMs.includes(vm.id)}
                    onSelect={handleSelectVM}
                    onDelete={handleDeleteSingle}
                    onView={handleViewVM}
                  />
                ))
              )}
            </div>
            
            {!loading && vms.length === 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-12 text-center"
              >
                <div className="w-20 h-20 mx-auto mb-6 flex items-center justify-center bg-[#020725]/50 rounded-2xl border border-[#bdccd4]/10">
                  <Server className="w-8 h-8 text-[#bdccd4]/30" />
                </div>
                <h3 className="text-[#bdccd4] font-medium mb-2">No VMs Found</h3>
                <p className="text-[#bdccd4]/40 text-sm max-w-md mx-auto mb-6">
                  Get started by creating your first virtual machine
                </p>
                <Button 
                  onClick={() => navigate('/admin/vms/new')}
                  className="bg-[#24ab94] hover:bg-[#24ab94]/90 text-black font-medium gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create VM
                </Button>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-[#020725] border-[#bdccd4]/10 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-[#bdccd4] flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              Confirm Delete
            </DialogTitle>
            <DialogDescription className="text-[#bdccd4]/60">
              Are you sure you want to delete <span className="text-[#bdccd4] font-medium">{vmToDelete?.name}</span>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button 
              variant="ghost" 
              onClick={() => setDeleteDialogOpen(false)}
              className="text-[#bdccd4]/60 w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleting}
              className="bg-red-500 hover:bg-red-600 w-full sm:w-auto"
            >
              {deleting && <span className="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-white/30 border-t-white" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
