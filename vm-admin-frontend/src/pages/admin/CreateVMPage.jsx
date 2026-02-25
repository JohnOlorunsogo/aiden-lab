import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Plus,
  Loader2,
  Zap,
  Server,
  Cpu,
  HardDrive,
  Box,
  Hash,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FloatingLabelInput } from '@/components/ui/floating-label-input';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { createVM, createBulkVMs } from '@/services/vmApi';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useTheme } from '@/lib/theme';

const cpuOptions = [
  { value: 1, label: '1 Core' },
  { value: 2, label: '2 Cores' },
  { value: 4, label: '4 Cores' },
  { value: 8, label: '8 Cores' },
];

const memoryOptions = [
  { value: 1, label: '1 Gi' },
  { value: 2, label: '2 Gi' },
  { value: 4, label: '4 Gi' },
  { value: 8, label: '8 Gi' },
  { value: 16, label: '16 Gi' },
];

const imageOptions = [
  { value: 'aiden_10-base:v1', label: 'aiden_10-base:v1' },
  { value: 'aiden_10-base:v2', label: 'aiden_10-base:v2' },
  { value: 'ubuntu:22.04', label: 'ubuntu:22.04' },
  { value: 'windows-server:2022', label: 'windows-server:2022' },
];

export default function CreateVMPage() {
  const { theme } = useTheme();
  const [formData, setFormData] = useState({
    name: '',
    cpu: 2,
    memory: 4,
    image: 'aiden_10-base:v1',
    quantity: 1
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!formData.name.trim()) {
      setError('VM name is required');
      return;
    }

    setCreating(true);
    try {
      if (formData.quantity > 1) {
        await createBulkVMs(
          formData.quantity,
          formData.name,
          formData.cpu,
          formData.memory,
          formData.image
        );
        toast.success(`Created ${formData.quantity} VMs successfully`);
      } else {
        await createVM(formData);
        toast.success(`Created ${formData.name} successfully`);
      }
      navigate('/admin');
    } catch (err) {
      setError('Failed to create VM');
      toast.error('Failed to create VM');
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError('');
  };

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
          
          <motion.h1 
            className="text-2xl md:text-3xl font-bold text-foreground mb-2 font-notch"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            Create VM
          </motion.h1>
          <motion.p 
            className="text-foreground/50 text-sm"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            Deploy a new virtual machine to your infrastructure
          </motion.p>
        </div>
      </div>

      <div className="max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-card/40 border-border backdrop-blur-md overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            
             <CardContent className="p-4 md:p-8">
               <form onSubmit={handleSubmit} className="space-y-6 md:space-y-8">
                 {error && (
                   <motion.div 
                     initial={{ opacity: 0, y: -10 }}
                     animate={{ opacity: 1, y: 0 }}
                     className="flex items-center gap-2 p-3 md:p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm"
                   >
                     <AlertCircle className="w-4 h-4 flex-shrink-0" />
                     {error}
                   </motion.div>
                 )}
 
                 <div className="space-y-5 md:space-y-6">
                   <div className="grid gap-4 md:gap-6 md:grid-cols-2">
                     <FloatingLabelInput
                       id="name"
                       label="VM Name"
                       value={formData.name}
                       onChange={(e) => handleChange('name', e.target.value)}
                       helperText="Used as prefix for multiple VMs (e.g., vm-1, vm-2)"
                     />
 
                     <FloatingLabelInput
                       id="quantity"
                       label="Quantity"
                       type="number"
                       min="1"
                       max="10"
                       value={formData.quantity}
                       onChange={(e) => handleChange('quantity', parseInt(e.target.value) || 1)}
                       helperText="Number of VMs to create (1-10)"
                     />
                   </div>
 
                   <div className="space-y-3">
                     <div className="flex items-center gap-2 text-foreground/70 text-sm">
                       <Cpu className="w-4 h-4 text-primary" />
                       <span>CPU Configuration</span>
                     </div>
                     <SegmentedControl
                       options={cpuOptions}
                       value={formData.cpu}
                       onChange={(value) => handleChange('cpu', value)}
                     />
                   </div>
 
                   <div className="space-y-3">
                     <div className="flex items-center gap-2 text-foreground/70 text-sm">
                       <HardDrive className="w-4 h-4 text-primary" />
                       <span>Memory Configuration</span>
                     </div>
                     <SegmentedControl
                       options={memoryOptions}
                       value={formData.memory}
                       onChange={(value) => handleChange('memory', value)}
                     />
                   </div>
 
                   <div className="space-y-3">
                     <div className="flex items-center gap-2 text-foreground/70 text-sm">
                       <Box className="w-4 h-4 text-primary" />
                       <span>Operating System Image</span>
                     </div>
                     <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                       {imageOptions.map((opt) => (
                         <button
                           key={opt.value}
                           type="button"
                           onClick={() => handleChange('image', opt.value)}
                           className={cn(
                             'relative px-3 md:px-4 py-3 rounded-lg border text-left text-sm transition-all duration-200',
                             formData.image === opt.value
                               ? 'bg-primary/10 border-primary text-primary'
                               : 'bg-background border-border text-foreground/70 hover:border-foreground/40'
                           )}
                         >
                           {formData.image === opt.value && (
                             <motion.div
                               layoutId="image-active"
                               className="absolute inset-0 border-2 border-primary rounded-lg"
                               transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                             />
                           )}
                           <span className="relative z-10 font-mono text-xs">{opt.label}</span>
                         </button>
                       ))}
                     </div>
                   </div>
                 </div>
 
                 <div className="pt-4 md:pt-6 flex flex-col sm:flex-row gap-3 border-t border-border">
                   <Button 
                     type="submit" 
                     disabled={creating}
                     className="bg-primary hover:bg-primary/90 text-black font-medium gap-2 w-full sm:w-auto"
                   >
                     {creating ? (
                       <>
                         <Loader2 className="w-4 h-4 animate-spin" />
                         Creating...
                       </>
                     ) : (
                       <>
                         <Zap className="w-4 h-4" />
                         Create {formData.quantity > 1 ? `${formData.quantity} VMs` : 'VM'}
                       </>
                     )}
                   </Button>
                   <Button 
                     type="button" 
                     variant="ghost"
                     onClick={() => navigate('/admin')}
                     className="text-foreground/60 hover:text-foreground hover:bg-foreground/5 w-full sm:w-auto"
                   >
                     Cancel
                   </Button>
                 </div>
               </form>
             </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
