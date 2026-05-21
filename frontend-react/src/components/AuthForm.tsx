import { useState } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { RegisterSchema, type AuthCredentials } from '../api/auth.schema';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function AuthForm({ type }: { type: 'register' }) {
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { setUser } = useAuth();
  
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<AuthCredentials>({
    resolver: zodResolver(RegisterSchema),
    defaultValues: {
      acceptTerms: false,
    },
  });

  const onSubmit = async (data: AuthCredentials) => {
    try {
      const res = await api.post('/auth/register', data);
      setUser(res.data);
      navigate(res.data.role === 'admin' ? '/admin' : '/dashboard', { replace: true });
    } catch (err: unknown) {
      const message = axios.isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;
      setError(message || 'Ошибка авторизации');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 bg-opacity-90">
      <form onSubmit={handleSubmit(onSubmit)} className="p-8 w-full max-w-md bg-white rounded-xl shadow-2xl space-y-4">
        <h2 className="text-2xl font-bold">{type === 'register' ? 'Регистрация' : 'Вход'}</h2>
        
        <div>
          <input {...register('email')} placeholder="Email" className="w-full p-2 border rounded" />
          {errors.email && <p className="text-red-500">{errors.email.message}</p>}
        </div>

        <div>
          <input {...register('password')} type="password" placeholder="Пароль" className="w-full p-2 border rounded" />
          {errors.password && <p className="text-red-500">{errors.password.message}</p>}
        </div>

        <label className="flex items-center space-x-2">
          <input type="checkbox" {...register('acceptTerms')} />
          <span>Согласен с условиями</span>
        </label>
        {errors.acceptTerms && <p className="text-red-500">{errors.acceptTerms.message}</p>}

        <div className="flex space-x-4">
          <button type="submit" disabled={isSubmitting} className="flex-1 bg-purple-600 text-white p-2 rounded hover:bg-purple-700">
            Зарегистрироваться
          </button>
          <button type="button" onClick={() => navigate('/')} className="flex-1 bg-gray-200 p-2 rounded">Отменить</button>
        </div>

        {error && <p className="text-red-600 font-bold">{error}</p>}
      </form>
    </div>
  );
}
