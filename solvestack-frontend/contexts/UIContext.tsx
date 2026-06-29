import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

type ToastVariant = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  title: string;
  message?: string;
  variant: ToastVariant;
}

interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: 'default' | 'danger';
}

interface UIContextValue {
  toast: (title: string, options?: { message?: string; variant?: ToastVariant }) => void;
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const UIContext = createContext<UIContextValue | undefined>(undefined);

export const UIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirmState, setConfirmState] = useState<(ConfirmOptions & { resolve: (value: boolean) => void }) | null>(null);

  const toast = useCallback((title: string, options?: { message?: string; variant?: ToastVariant }) => {
    const id = Date.now() + Math.random();
    const nextToast: Toast = {
      id,
      title,
      message: options?.message,
      variant: options?.variant || 'info',
    };
    setToasts(prev => [...prev, nextToast]);
    window.setTimeout(() => {
      setToasts(prev => prev.filter(item => item.id !== id));
    }, 4200);
  }, []);

  const confirm = useCallback((options: ConfirmOptions) => (
    new Promise<boolean>(resolve => {
      setConfirmState({ ...options, resolve });
    })
  ), []);

  const closeConfirm = (value: boolean) => {
    if (!confirmState) return;
    confirmState.resolve(value);
    setConfirmState(null);
  };

  const value = useMemo(() => ({ toast, confirm }), [toast, confirm]);

  return (
    <UIContext.Provider value={value}>
      {children}

      <div className="fixed right-4 top-4 z-[100] flex w-[min(380px,calc(100vw-2rem))] flex-col gap-3">
        {toasts.map(item => {
          const Icon = item.variant === 'success' ? CheckCircle2 : item.variant === 'error' ? AlertTriangle : Info;
          const tone = item.variant === 'success'
            ? 'border-emerald-400/20 text-emerald-200'
            : item.variant === 'error'
              ? 'border-red-400/20 text-red-200'
              : 'border-champagne/20 text-platinum';
          return (
            <div key={item.id} className={`luxury-surface rounded-xl p-4 ${tone}`}>
              <div className="flex items-start gap-3">
                <Icon className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-white">{item.title}</p>
                  {item.message && <p className="mt-1 text-xs leading-relaxed text-white/50">{item.message}</p>}
                </div>
                <button
                  onClick={() => setToasts(prev => prev.filter(toastItem => toastItem.id !== item.id))}
                  className="rounded-md p-1 text-white/30 hover:bg-white/10 hover:text-white"
                  aria-label="Dismiss notification"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {confirmState && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <div className="luxury-surface w-full max-w-md rounded-2xl p-6">
            <div className="mb-5 flex items-start gap-4">
              <div className={`rounded-xl p-3 ${confirmState.tone === 'danger' ? 'bg-red-500/10 text-red-300' : 'bg-champagne/10 text-champagne'}`}>
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">{confirmState.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-white/50">{confirmState.message}</p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => closeConfirm(false)}
                className="rounded-xl border border-white/10 px-4 py-2 text-sm font-bold text-white/60 hover:bg-white/5 hover:text-white"
              >
                {confirmState.cancelLabel || 'Cancel'}
              </button>
              <button
                onClick={() => closeConfirm(true)}
                className={`rounded-xl px-4 py-2 text-sm font-bold ${confirmState.tone === 'danger' ? 'bg-red-500 text-white hover:bg-red-400' : 'bg-white text-black hover:bg-champagne'}`}
              >
                {confirmState.confirmLabel || 'Continue'}
              </button>
            </div>
          </div>
        </div>
      )}
    </UIContext.Provider>
  );
};

export const useUI = () => {
  const context = useContext(UIContext);
  if (!context) {
    throw new Error('useUI must be used within UIProvider');
  }
  return context;
};
