import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import CreateVMPage from './pages/admin/CreateVMPage';
import VMDetailsPage from './pages/admin/VMDetailsPage';

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-background">
        <Routes>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="vms/new" element={<CreateVMPage />} />
            <Route path="vms/:id" element={<VMDetailsPage />} />
          </Route>
          <Route path="/" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="vms/new" element={<CreateVMPage />} />
            <Route path="vms/:id" element={<VMDetailsPage />} />
          </Route>
        </Routes>
      </div>
      <Toaster 
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            color: 'hsl(var(--foreground))',
          },
        }}
      />
    </BrowserRouter>
  );
}

export default App;
