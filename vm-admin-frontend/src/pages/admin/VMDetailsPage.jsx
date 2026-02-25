import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Server, 
  Cpu, 
  HardDrive, 
  Image, 
  Network, 
  Clock,
  Copy,
  Check,
  Loader2,
  Terminal,
  Activity,
  Calendar,
  ExternalLink,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { StatusBadge } from '@/components/ui/status-badge';
import { fetchVM } from '@/services/vmApi';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useTheme } from '@/lib/theme';

function CopyableField({ value, label, className }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (value) {
      try {
        await navigator.clipboard.writeText(value);
        setCopied(true);
        toast.success(`${label} copied to clipboard`);
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        toast.error('Failed to copy to clipboard');
      }
    }
  };

  if (!value) return <span className="text-foreground/30">-</span>;

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'flex items-center gap-2 font-mono text-sm transition-all duration-200',
        'text-foreground/80 hover:text-primary',
        className
      )}
    >
      <span>{value}</span>
      {copied ? (
        <Check className="w-3 h-3 text-primary" />
      ) : (
        <Copy className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </button>
  );
}

function InfoRow({ icon, label, value, copyable = false }) {
  const IconComp = icon;
  return (
    <div className="group flex items-center justify-between py-3 border-b border-foreground/5 last:border-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <IconComp className="w-4 h-4 text-primary" />
        </div>
        <span className="text-foreground/60 text-sm">{label}</span>
      </div>
      <div>
        {copyable ? (
          <CopyableField value={value} label={label} />
        ) : (
          <span className="text-foreground text-sm font-medium">{value || '-'}</span>
        )}
      </div>
    </div>
  );
}

function BentoCard({ children, className, delay = 0, glow = false }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className={cn(
        'relative overflow-hidden rounded-xl bg-card/60 border border-border',
        'backdrop-blur-sm transition-all duration-300',
        'hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5',
        className
      )}
    >
      {glow && (
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5 opacity-50" />
      )}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      {children}
    </motion.div>
  );
}

export default function VMDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [vm, setVM] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [connectionCopied, setConnectionCopied] = useState(false);

  useEffect(() => {
    fetchVM(id)
      .then(setVM)
      .catch(() => {
        setError('VM not found');
        toast.error('VM not found');
      })
      .finally(() => setLoading(false));
  }, [id]);

  const connectionString = vm?.externalIP && vm?.rdpPort 
    ? `${vm.externalIP}:${vm.rdpPort}` 
    : null;

  const handleCopyConnection = async () => {
    if (connectionString) {
      try {
        await navigator.clipboard.writeText(connectionString);
        toast.success('Connection string copied to clipboard');
      } catch (error) {
        toast.error('Failed to copy connection string');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error || !vm) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Button 
          variant="ghost" 
          onClick={() => navigate('/admin')}
          className="mb-4 text-foreground/60 hover:text-foreground hover:bg-foreground/5 -ml-2"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
        <div className="p-12 text-center bg-card/30 border border-border rounded-xl">
          <div className="w-20 h-20 mx-auto mb-6 flex items-center justify-center bg-red-500/10 rounded-2xl border border-red-500/20">
            <Server className="w-8 h-8 text-red-400" />
          </div>
          <h3 className="text-foreground font-medium mb-2">VM Not Found</h3>
          <p className="text-foreground/40 text-sm">The requested virtual machine could not be found</p>
        </div>
      </motion.div>
    );
  }

  return (
    <div>
       <div className="relative -mx-4 md:-mx-8 -mt-4 md:-mt-8 mb-8 px-4 md:px-8 pt-6 md:pt-8 pb-10 overflow-hidden">
        <div 
          className="absolute inset-0 bg-card"
          style={{
            backgroundImage: `url('/Aiden lab Assets (Png & SVG)/Patterns/Asset 18.svg')`,
            backgroundSize: '600px',
            backgroundPosition: 'center',
            opacity: theme === 'dark' ? 0.15 : 0.05
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-card/50 to-card" />
        
        <div className="relative z-10">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/admin')}
            className="mb-4 text-foreground/60 hover:text-foreground hover:bg-foreground/5 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <motion.h1 
                  className="text-2xl md:text-3xl font-bold text-foreground font-notch"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  {vm.name}
                </motion.h1>
                <StatusBadge status={vm.status} />
              </div>
              <motion.p 
                className="text-foreground/50 text-sm"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                Virtual Machine Details & Configuration
              </motion.p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        {connectionString && (
          <BentoCard 
            className="lg:col-span-2 glow-effect" 
            delay={0.1}
            glow
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-primary font-bold flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Connection String
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <code className="text-lg md:text-2xl font-mono text-foreground tracking-wider break-all">
                  {connectionString}
                </code>
                <Button 
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    handleCopyConnection();
                    setConnectionCopied(true);
                    setTimeout(() => setConnectionCopied(false), 2000);
                  }}
                  className={cn(
                    "border-primary/30 hover:bg-primary/10 hover:text-primary w-full sm:w-auto transition-all duration-200",
                    connectionCopied ? "text-primary bg-primary/10" : "text-primary"
                  )}
                >
                  {connectionCopied ? (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              <p className="text-xs text-foreground/40 mt-4 flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                Use this address to connect via RDP client
              </p>
            </CardContent>
          </BentoCard>
        )}

        <BentoCard delay={0.15}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-primary font-bold flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Status Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-foreground/60 text-sm">Current State</span>
                <StatusBadge status={vm.status} />
              </div>
              <Separator className="bg-foreground/10" />
              <div className="flex items-center justify-between">
                <span className="text-foreground/60 text-sm">Uptime</span>
                <span className="text-foreground font-mono text-sm">{vm.uptime}</span>
              </div>
            </div>
          </CardContent>
        </BentoCard>

        <BentoCard delay={0.2}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-primary font-bold flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Hardware
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <InfoRow icon={Cpu} label="CPU Cores" value={`${vm.cpu} cores`} />
            <InfoRow icon={HardDrive} label="Memory" value={`${vm.memory} GiB`} />
            <InfoRow icon={Image} label="Image" value={vm.image} />
          </CardContent>
        </BentoCard>

        <BentoCard delay={0.25}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-primary font-bold flex items-center gap-2">
              <Network className="w-4 h-4" />
              Network
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <InfoRow icon={Network} label="Internal IP" value={vm.internalIP} copyable />
            <InfoRow icon={Network} label="External IP" value={vm.externalIP} copyable />
            <InfoRow icon={Shield} label="RDP Port" value={vm.rdpPort?.toString()} />
          </CardContent>
        </BentoCard>

        <BentoCard delay={0.3}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-primary font-bold flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Metadata
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <InfoRow icon={Calendar} label="Created" value={new Date(vm.createdAt).toLocaleString()} />
            <InfoRow icon={Server} label="VM ID" value={vm.id} copyable />
          </CardContent>
        </BentoCard>
      </div>
    </div>
  );
}
