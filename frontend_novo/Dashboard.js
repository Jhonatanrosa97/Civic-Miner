"import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  FileText,
  Search,
  Download,
  Trash2,
  Sun,
  Moon,
  LogOut,
  Filter,
  Calendar,
  MapPin,
  FileDown,
  TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [cityInput, setCityInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [files, setFiles] = useState([]);
  const [stats, setStats] = useState({ total_files: 0, total_cities: 0, files_today: 0 });
  const [scraperProgress, setScraperProgress] = useState(null);
  const [isScrapingActive, setIsScrapingActive] = useState(false);
  const [filterCity, setFilterCity] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/');
    } else {
      fetchFiles();
      fetchStats();
    }
  }, [user, navigate]);

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API}/files?limit=10`);
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const searchCities = useCallback(async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await axios.get(`${API}/cities/search?q=${query}`);
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error searching cities:', error);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      searchCities(cityInput);
    }, 300);

    return () => clearTimeout(timer);
  }, [cityInput, searchCities]);

  const startScraper = async (cityName) => {
    try {
      setIsScrapingActive(true);
      setScraperProgress({ progress: 0, status: 'iniciando', message: 'Iniciando scraper...' });
      
      await axios.post(`${API}/scraper/start`, { city_name: cityName });
      
      // Poll progress
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/scraper/progress/${cityName}`);
          setScraperProgress(response.data);
          
          if (response.data.progress === 100) {
            clearInterval(interval);
            setIsScrapingActive(false);
            toast.success('Download concluído!');
            fetchFiles();
            fetchStats();
            setCityInput('');
            setShowSuggestions(false);
          }
        } catch (error) {
          clearInterval(interval);
          setIsScrapingActive(false);
          toast.error('Erro ao buscar progresso');
        }
      }, 1000);

    } catch (error) {
      setIsScrapingActive(false);
      toast.error('Erro ao iniciar scraper');
    }
  };

  const handleCitySelect = (city) => {
    setCityInput(city);
    setShowSuggestions(false);
    startScraper(city);
  };

  const clearAllFiles = async () => {
    try {
      await axios.delete(`${API}/files/clear`);
      setFiles([]);
      fetchStats();
      toast.success('Todos os arquivos foram removidos');
    } catch (error) {
      toast.error('Erro ao limpar arquivos');
    }
  };

  const filterFilesByCity = async () => {
    if (!filterCity) {
      fetchFiles();
      return;
    }

    try {
      const response = await axios.post(`${API}/files/filter`, {
        city_name: filterCity
      });
      setFiles(response.data);
    } catch (error) {
      toast.error('Erro ao filtrar arquivos');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className=\"min-h-screen bg-background\">
      {/* Header */}
      <header className=\"border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50\">
        <div className=\"container mx-auto px-6 py-4\">
          <div className=\"flex items-center justify-between\">
            <div className=\"flex items-center gap-3\">
              <div className=\"p-2 rounded-xl bg-primary/10\">
                <FileText className=\"w-6 h-6 text-primary\" />
              </div>
              <div>
                <h1 className=\"text-xl font-heading font-bold tracking-tight\">CityContract</h1>
                <p className=\"text-xs text-muted-foreground\">Olá, {user?.name}</p>
              </div>
            </div>
            
            <div className=\"flex items-center gap-3\">
              <Button
                variant=\"ghost\"
                size=\"icon\"
                onClick={toggleTheme}
                data-testid=\"theme-toggle-button\"
                className=\"rounded-full\"
              >
                {theme === 'light' ? <Moon className=\"w-5 h-5\" /> : <Sun className=\"w-5 h-5\" />}
              </Button>
              <Button
                variant=\"ghost\"
                size=\"icon\"
                onClick={handleLogout}
                data-testid=\"logout-button\"
                className=\"rounded-full\"
              >
                <LogOut className=\"w-5 h-5\" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className=\"container mx-auto px-6 py-8\">
        {/* Stats Cards */}
        <div className=\"grid grid-cols-1 md:grid-cols-3 gap-6 mb-8\">
          <Card className=\"p-6 hover:shadow-lg transition-shadow duration-300\" data-testid=\"total-files-stat\">
            <div className=\"flex items-center justify-between\">
              <div>
                <p className=\"text-sm text-muted-foreground mb-1\">Total de Arquivos</p>
                <p className=\"text-3xl font-heading font-bold\">{stats.total_files}</p>
              </div>
              <div className=\"p-3 rounded-xl bg-primary/10\">
                <FileDown className=\"w-6 h-6 text-primary\" />
              </div>
            </div>
          </Card>

          <Card className=\"p-6 hover:shadow-lg transition-shadow duration-300\" data-testid=\"total-cities-stat\">
            <div className=\"flex items-center justify-between\">
              <div>
                <p className=\"text-sm text-muted-foreground mb-1\">Cidades Diferentes</p>
                <p className=\"text-3xl font-heading font-bold\">{stats.total_cities}</p>
              </div>
              <div className=\"p-3 rounded-xl bg-primary/10\">
                <MapPin className=\"w-6 h-6 text-primary\" />
              </div>
            </div>
          </Card>

          <Card className=\"p-6 hover:shadow-lg transition-shadow duration-300\" data-testid=\"files-today-stat\">
            <div className=\"flex items-center justify-between\">
              <div>
                <p className=\"text-sm text-muted-foreground mb-1\">Downloads Hoje</p>
                <p className=\"text-3xl font-heading font-bold\">{stats.files_today}</p>
              </div>
              <div className=\"p-3 rounded-xl bg-primary/10\">
                <TrendingUp className=\"w-6 h-6 text-primary\" />
              </div>
            </div>
          </Card>
        </div>

        {/* Main Grid */}
        <div className=\"grid grid-cols-1 lg:grid-cols-12 gap-6\">
          {/* Search Section */}
          <Card className=\"lg:col-span-8 lg:row-span-2 p-8 hover:shadow-lg transition-shadow duration-300\">
            <div className=\"space-y-6\">
              <div className=\"space-y-2\">
                <h2 className=\"text-2xl font-heading font-bold tracking-tight\">
                  Buscar Contratos
                </h2>
                <p className=\"text-muted-foreground\">
                  Digite o nome da cidade para baixar o contrato automaticamente
                </p>
              </div>

              {/* Search Input with Autocomplete */}
              <div className=\"relative\">
                <div className=\"relative\">
                  <Search className=\"absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground\" />
                  <Input
                    data-testid=\"city-search-input\"
                    type=\"text\"
                    placeholder=\"Digite o nome da cidade...\"
                    value={cityInput}
                    onChange={(e) => {
                      setCityInput(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    disabled={isScrapingActive}
                    className=\"h-14 pl-12 pr-4 text-lg rounded-xl border-2 focus-visible:ring-2 transition-all\"
                  />
                </div>

                {/* Autocomplete Suggestions */}
                {showSuggestions && suggestions.length > 0 && (
                  <Card className=\"absolute w-full mt-2 p-2 z-50 shadow-lg\" data-testid=\"city-suggestions\">
                    <ScrollArea className=\"max-h-60\">
                      {suggestions.map((city, index) => (
                        <button
                          key={index}
                          data-testid={`city-suggestion-${index}`}
                          onClick={() => handleCitySelect(city)}
                          disabled={isScrapingActive}
                          className=\"w-full text-left px-4 py-3 rounded-lg hover:bg-accent transition-colors duration-200 flex items-center gap-3\"
                        >
                          <MapPin className=\"w-4 h-4 text-muted-foreground\" />
                          <span>{city}</span>
                        </button>
                      ))}
                    </ScrollArea>
                  </Card>
                )}
              </div>

              {/* Progress Section */}
              {scraperProgress && isScrapingActive && (
                <div className=\"space-y-4 p-6 rounded-xl bg-muted/50\" data-testid=\"scraper-progress-section\">
                  <div className=\"flex items-center justify-between\">
                    <div>
                      <p className=\"font-medium\">Status do Scraper</p>
                      <p className=\"text-sm text-muted-foreground\">{scraperProgress.message}</p>
                    </div>
                    <p className=\"text-2xl font-heading font-bold\" data-testid=\"progress-percentage\">
                      {scraperProgress.progress}%
                    </p>
                  </div>
                  <Progress value={scraperProgress.progress} className=\"h-3\" />
                </div>
              )}

              {/* Info Cards */}
              <div className=\"grid grid-cols-1 md:grid-cols-2 gap-4 pt-4\">
                <div className=\"p-4 rounded-xl bg-primary/5 border border-primary/20\">
                  <p className=\"text-sm font-medium text-primary mb-1\">Automático</p>
                  <p className=\"text-xs text-muted-foreground\">
                    O download inicia assim que você selecionar uma cidade
                  </p>
                </div>
                <div className=\"p-4 rounded-xl bg-primary/5 border border-primary/20\">
                  <p className=\"text-sm font-medium text-primary mb-1\">Rápido</p>
                  <p className=\"text-xs text-muted-foreground\">
                    Processo otimizado para máxima velocidade
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Files Section */}
          <Card className=\"lg:col-span-4 lg:row-span-2 p-6 hover:shadow-lg transition-shadow duration-300\">
            <div className=\"space-y-4\">
              <div className=\"flex items-center justify-between\">
                <h2 className=\"text-xl font-heading font-bold tracking-tight\">
                  Arquivos Baixados
                </h2>
                <Button
                  variant=\"ghost\"
                  size=\"icon\"
                  onClick={clearAllFiles}
                  data-testid=\"clear-all-files-button\"
                  className=\"rounded-full\"
                >
                  <Trash2 className=\"w-4 h-4\" />
                </Button>
              </div>

              {/* Filter */}
              <div className=\"relative\">
                <Filter className=\"absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground\" />
                <Input
                  data-testid=\"filter-city-input\"
                  placeholder=\"Filtrar por cidade...\"
                  value={filterCity}
                  onChange={(e) => setFilterCity(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && filterFilesByCity()}
                  className=\"pl-10 h-10\"
                />
              </div>

              {/* Files List */}
              <ScrollArea className=\"h-[500px]\">
                <div className=\"space-y-3\" data-testid=\"files-list\">
                  {files.length === 0 ? (
                    <div className=\"text-center py-12\">
                      <Download className=\"w-12 h-12 text-muted-foreground mx-auto mb-3\" />
                      <p className=\"text-sm text-muted-foreground\">
                        Nenhum arquivo baixado ainda
                      </p>
                    </div>
                  ) : (
                    files.map((file, index) => (
                      <div
                        key={file.id}
                        data-testid={`file-item-${index}`}
                        className=\"p-4 rounded-lg border bg-card hover:bg-accent/50 transition-all duration-200 group\"
                      >
                        <div className=\"flex items-start justify-between gap-3\">
                          <div className=\"flex-1 min-w-0\">
                            <p className=\"font-medium text-sm truncate mb-1\">
                              {file.city_name}
                            </p>
                            <p className=\"text-xs text-muted-foreground truncate mb-2\">
                              {file.file_name}
                            </p>
                            <div className=\"flex items-center gap-2 text-xs text-muted-foreground\">
                              <Calendar className=\"w-3 h-3\" />
                              <span>
                                {format(new Date(file.download_date), \"dd/MM/yyyy 'às' HH:mm\", { locale: ptBR })}
                              </span>
                            </div>
                          </div>
                          <Button
                            size=\"icon\"
                            variant=\"ghost\"
                            data-testid={`view-file-button-${index}`}
                            className=\"rounded-full shrink-0 opacity-0 group-hover:opacity-100 transition-opacity\"
                          >
                            <FileText className=\"w-4 h-4\" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
"