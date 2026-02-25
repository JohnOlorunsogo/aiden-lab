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

function CopyableField({ value, label, className }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    console.log('CopyableField handleCopy called');
    console.log('Value:', value);
    if (value) {
      try {
        if (navigator.clipboard && window.isSecureContext) {
          // Use modern clipboard API if available (HTTPS or localhost)
          await navigator.clipboard.writeText(value);
        } else {
          // Fallback for HTTP or older browsers
          const textArea = document.createElement('textarea');
          textArea.value = value;
          textArea.style.position = 'fixed';
          textArea.style.top = '0';
          textArea.style.left = '0';
          textArea.style.width = '2em';
          textArea.style.height = '2em';
          textArea.style.padding = '0';
          textArea.style.border = 'none';
          textArea.style.outline = 'none';
          textArea.style.boxShadow = 'none';
          textArea.style.background = 'transparent';
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          document.execCommand('copy');
          document.body.removeChild(textArea);
        }
        console.log('Copy successful');
        setCopied(true);
        toast.success(`${label} copied to clipboard`);
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.error('Copy failed:', error);
        toast.error('Failed to copy to clipboard');
      }
    }
  };

  if (!value) return <span className="text-[#bdccd4]/30">-</span>;

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'flex items-center gap-2 font-mono text-sm transition-all duration-200',
        'text-[#bdccd4]/80 hover:text-[#24ab94]',
        className
      )}
    >
      <span>{value}</span>
      {copied ? (
        <Check className="w-3 h-3 text-[#24ab94]" />
      ) : (
        <Copy className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </button>
  );
}

function InfoRow({ icon, label, value, copyable = false }) {
  const IconComp = icon;
  return (
    <div className="group flex items-center justify-between py-3 border-b border-[#bdccd4]/5 last:border-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#24ab94]/10 flex items-center justify-center">
          <IconComp className="w-4 h-4 text-[#24ab94]" />
        </div>
        <span className="text-[#bdccd4]/60 text-sm">{label}</span>
      </div>
      <div>
        {copyable ? (
          <CopyableField value={value} label={label} />
        ) : (
          <span className="text-[#bdccd4] text-sm font-medium">{value || '-'}</span>
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
        'relative overflow-hidden rounded-xl bg-[#020725]/60 border border-[#bdccd4]/10',
        'backdrop-blur-sm transition-all duration-300',
        'hover:border-[#24ab94]/20 hover:shadow-lg hover:shadow-[#24ab94]/5',
        className
      )}
    >
      {glow && (
        <div className="absolute inset-0 bg-gradient-to-br from-[#24ab94]/10 via-transparent to-[#24ab94]/5 opacity-50" />
      )}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#24ab94]/20 to-transparent" />
      {children}
    </motion.div>
  );
}

export default function VMDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
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
    console.log('handleCopyConnection called');
    console.log('Connection string:', connectionString);
    if (connectionString) {
      try {
        if (navigator.clipboard && window.isSecureContext) {
          // Use modern clipboard API if available (HTTPS or localhost)
          await navigator.clipboard.writeText(connectionString);
        } else {
          // Fallback for HTTP or older browsers
          const textArea = document.createElement('textarea');
          textArea.value = connectionString;
          textArea.style.position = 'fixed';
          textArea.style.top = '0';
          textArea.style.left = '0';
          textArea.style.width = '2em';
          textArea.style.height = '2em';
          textArea.style.padding = '0';
          textArea.style.border = 'none';
          textArea.style.outline = 'none';
          textArea.style.boxShadow = 'none';
          textArea.style.background = 'transparent';
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          document.execCommand('copy');
          document.body.removeChild(textArea);
        }
        console.log('Copy successful');
        toast.success('Connection string copied to clipboard');
      } catch (error) {
        console.error('Copy failed:', error);
        toast.error('Failed to copy connection string');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-[#24ab94] animate-spin" />
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
          className="mb-4 text-[#bdccd4]/60 hover:text-[#bdccd4] hover:bg-[#bdccd4]/5 -ml-2"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
        <div className="p-12 text-center bg-[#020725]/30 border border-[#bdccd4]/10 rounded-xl">
          <div className="w-20 h-20 mx-auto mb-6 flex items-center justify-center bg-red-500/10 rounded-2xl border border-red-500/20">
            <Server className="w-8 h-8 text-red-400" />
          </div>
          <h3 className="text-[#bdccd4] font-medium mb-2">VM Not Found</h3>
          <p className="text-[#bdccd4]/40 text-sm">The requested virtual machine could not be found</p>
        </div>
      </motion.div>
    );
  }

  return (
    <div>
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
        
        <div className="relative z-10">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/admin')}
            className="mb-4 text-[#bdccd4]/60 hover:text-[#bdccd4] hover:bg-[#bdccd4]/5 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <motion.h1 
                  className="text-2xl md:text-3xl font-bold text-[#bdccd4] font-notch"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  {vm.name}
                </motion.h1>
                <StatusBadge status={vm.status} />
              </div>
              <motion.p 
                className="text-[#bdccd4]/50 text-sm"
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
              <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Connection String
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <code className="text-lg md:text-2xl font-mono text-[#bdccd4] tracking-wider break-all">
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
                    "border-[#24ab94]/30 hover:bg-[#24ab94]/10 hover:text-[#24ab94] w-full sm:w-auto transition-all duration-200",
                    connectionCopied ? "text-[#24ab94] bg-[#24ab94]/10" : "text-[#24ab94]"
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
              <p className="text-xs text-[#bdccd4]/40 mt-4 flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                Use this address to connect via RDP client
              </p>
            </CardContent>
          </BentoCard>
        )}

        <BentoCard delay={0.15}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Status Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[#bdccd4]/60 text-sm">Current State</span>
                <StatusBadge status={vm.status} />
              </div>
              <Separator className="bg-[#bdccd4]/10" />
              <div className="flex items-center justify-between">
                <span className="text-[#bdccd4]/60 text-sm">Uptime</span>
                <span className="text-[#bdccd4] font-mono text-sm">{vm.uptime}</span>
              </div>
            </div>
          </CardContent>
        </BentoCard>

        <BentoCard delay={0.2}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
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
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
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
            <CardTitle className="text-xs md:text-sm uppercase tracking-wider text-[#24ab94] font-bold flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Metadata
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <InfoRow icon={Calendar} label="Created" value={new Date(vm.createdAt).toLocaleString()} />
            <InfoRow icon={Clock} label="Last Updated" value={new Date(vm.updatedAt).toLocaleString()} />
            <InfoRow icon={Server} label="VM ID" value={vm.id} copyable />
          </CardContent>
        </BentoCard>
      </div>
    </div>
  );
}
