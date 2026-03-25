"import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { FileText, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(formData.email, formData.password);
    } else {
      result = await register(formData.name, formData.email, formData.password);
    }

    setLoading(false);

    if (result.success) {
      toast.success(isLogin ? 'Login realizado com sucesso!' : 'Conta criada com sucesso!');
      navigate('/dashboard');
    } else {
      toast.error(result.message);
    }
  };

  return (
    <div className=\"min-h-screen grid lg:grid-cols-2\">
      {/* Left Side - Form */}
      <div className=\"flex items-center justify-center p-8 lg:p-12\">
        <div className=\"w-full max-w-md space-y-8\">
          {/* Logo and Title */}
          <div className=\"space-y-3\">
            <div className=\"flex items-center gap-3\">
              <div className=\"p-3 rounded-2xl bg-primary/10\">
                <FileText className=\"w-8 h-8 text-primary\" />
              </div>
              <h1 className=\"text-3xl font-heading font-bold tracking-tight text-foreground\">
                CityContract
              </h1>
            </div>
            <div className=\"space-y-1\">
              <h2 className=\"text-2xl font-heading font-bold tracking-tight\">
                {isLogin ? 'Bem-vindo de volta' : 'Criar nova conta'}
              </h2>
              <p className=\"text-muted-foreground\">
                {isLogin
                  ? 'Entre com suas credenciais para continuar'
                  : 'Preencha os dados para criar sua conta'}
              </p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className=\"space-y-6\">
            {!isLogin && (
              <div className=\"space-y-2\">
                <Label htmlFor=\"name\" className=\"text-sm font-medium\">
                  Nome completo
                </Label>
                <Input
                  id=\"name\"
                  data-testid=\"register-name-input\"
                  type=\"text\"
                  placeholder=\"Seu nome\"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className=\"h-12 rounded-lg\"
                />
              </div>
            )}

            <div className=\"space-y-2\">
              <Label htmlFor=\"email\" className=\"text-sm font-medium\">
                Email
              </Label>
              <Input
                id=\"email\"
                data-testid=\"login-email-input\"
                type=\"email\"
                placeholder=\"seu@email.com\"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className=\"h-12 rounded-lg\"
              />
            </div>

            <div className=\"space-y-2\">
              <Label htmlFor=\"password\" className=\"text-sm font-medium\">
                Senha
              </Label>
              <div className=\"relative\">
                <Input
                  id=\"password\"
                  data-testid=\"login-password-input\"
                  type={showPassword ? 'text' : 'password'}
                  placeholder=\"••••••••\"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className=\"h-12 rounded-lg pr-12\"
                />
                <button
                  type=\"button\"
                  onClick={() => setShowPassword(!showPassword)}
                  className=\"absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors\"
                  data-testid=\"toggle-password-visibility\"
                >
                  {showPassword ? <EyeOff className=\"w-5 h-5\" /> : <Eye className=\"w-5 h-5\" />}
                </button>
              </div>
            </div>

            <Button
              type=\"submit\"
              data-testid=\"login-submit-button\"
              disabled={loading}
              className=\"w-full h-12 rounded-full text-base font-medium shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all active:scale-95\"
            >
              {loading ? 'Carregando...' : isLogin ? 'Entrar' : 'Criar conta'}
            </Button>
          </form>

          {/* Toggle between login/register */}
          <div className=\"text-center\">
            <button
              type=\"button\"
              data-testid=\"toggle-auth-mode\"
              onClick={() => {
                setIsLogin(!isLogin);
                setFormData({ name: '', email: '', password: '' });
              }}
              className=\"text-sm text-muted-foreground hover:text-primary transition-colors font-medium\"
            >
              {isLogin ? (
                <>
                  Não tem uma conta?{' '}
                  <span className=\"text-primary\">Criar conta</span>
                </>
              ) : (
                <>
                  Já tem uma conta?{' '}
                  <span className=\"text-primary\">Fazer login</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Right Side - Image */}
      <div className=\"hidden lg:block relative overflow-hidden bg-muted\">
        <div className=\"absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-transparent z-10\" />
        <img
          src=\"https://images.unsplash.com/photo-1707672705875-cfb33db1a60d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjaXR5JTIwYXJjaGl0ZWN0dXJlJTIwYWJzdHJhY3R8ZW58MHx8fHwxNzY5NDM0NDE4fDA&ixlib=rb-4.1.0&q=85\"
          alt=\"Modern city architecture\"
          className=\"w-full h-full object-cover\"
        />
        <div className=\"absolute bottom-0 left-0 right-0 p-12 z-20 bg-gradient-to-t from-background/80 to-transparent\">
          <h3 className=\"text-3xl font-heading font-bold text-foreground mb-3\">
            Gerencie contratos de cidades
          </h3>
          <p className=\"text-lg text-muted-foreground\">
            Busque, baixe e organize contratos de múltiplas cidades de forma eficiente e profissional.
          </p>
        </div>
      </div>
    </div>
  );
}
"