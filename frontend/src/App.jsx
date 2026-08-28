import { useState, useEffect, useRef } from 'react';
import { login, getHistory, sendMessage } from './api';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (token) {
      getHistory(token).then(data => setMessages(data.messages || []));
    }
  }, [token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await login(username, password);
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
    } catch (error) {
      alert('Login falhou. Tente user_normal com senha 123456');
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const data = await sendMessage(userMsg, token);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      alert('Erro ao comunicar com o backend MCP.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    setMessages([]);
  };

  // Função para converter **texto** em negrito no React
  const formatMessage = (text) => {
    if (!text) return "";
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  if (!token) {
    return (
      <div className="login-container">
        <h2>ChatPay Login 🔒</h2>
        <form onSubmit={handleLogin}>
          <input placeholder="Usuário" value={username} onChange={e => setUsername(e.target.value)} required />
          <input type="password" placeholder="Senha" value={password} onChange={e => setPassword(e.target.value)} required />
          <button type="submit">Entrar</button>
        </form>
        <p style={{fontSize: '14px', color: '#666'}}>
          <b>Usuários de teste:</b><br/>
          <code>user_normal</code> (Limite alto)<br/>
          <code>user_baixo</code> (Limite baixo)<br/>
          Senha para ambos: <code>123456</code>
        </p>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="header">
        <h2>ChatPay 🛒</h2>
        <button onClick={handleLogout}>Sair</button>
      </div>
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <strong>{m.role === 'user' ? 'Você' : 'Agente'}:</strong>

            {/* Aqui renderizamos o texto formatado sem os asteriscos */}
            <p style={{ whiteSpace: 'pre-wrap' }}>{formatMessage(m.content)}</p>

          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <em>Processando ferramentas MCP... ⚙️</em>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      <form className="input-area" onSubmit={handleSend}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Enviar mensagem"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>➤</button>
      </form>
    </div>
  );
}

export default App;