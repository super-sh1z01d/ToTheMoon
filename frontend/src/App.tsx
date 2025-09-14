import { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { HomePage } from './pages/HomePage';
import { AdminPage } from './pages/AdminPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    },
  },
});

function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'admin'>('home');

  const renderPage = () => {
    switch (currentPage) {
      case 'admin':
        return <AdminPage />;
      case 'home':
      default:
        return <HomePage onNavigateToAdmin={() => setCurrentPage('admin')} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              <button
                onClick={() => setCurrentPage('home')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  currentPage === 'home'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Главная
              </button>
              <button
                onClick={() => setCurrentPage('admin')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  currentPage === 'admin'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Админ-панель
              </button>
            </div>
          </div>
        </nav>
        
        {renderPage()}
      </div>
    </QueryClientProvider>
  );
}

export default App;
