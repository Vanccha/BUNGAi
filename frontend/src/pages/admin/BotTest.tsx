import { api } from '../../api/client'
import { ChatPanel } from '../../components/ChatPanel'
import { useAsync } from '../../lib/useAsync'
import { PageHead } from './AdminLayout'

export default function BotTestPage() {
  const { data } = useAsync(() => api.admin.getSettings(), [])
  return (
    <>
      <PageHead title="Bot Test" desc="Bilgi bankasında veya ayarlarda yaptığınız değişiklikleri burada hemen deneyin. Bu sohbet müşteri sohbetlerinden ayrıdır; ancak rezervasyon oluşturursa gerçek kayıt oluşabilir." />
      <div className="max-w-xl rounded-3xl overflow-hidden shadow-xl border border-pool-200">
        <ChatPanel
          className="h-[70vh] min-h-[420px]"
          send={api.admin.chatTest}
          botName={data?.bot_name ?? 'Asistan'}
          welcome={data?.bot_welcome_message ?? 'Merhaba! Size nasıl yardımcı olabilirim?'}
          storageKey="bungai_admin_test_session"
        />
      </div>
    </>
  )
}
