import { useState } from 'react';
import { useDPDPStore } from '../stores/dpdpStore';
import { t } from '../i18n'

export function DPDPWithdrawalPanel() {
  const { consents, withdrawConsent, isWithdrawalMode, setWithdrawalMode } = useDPDPStore();
  const [confirmWithdraw, setConfirmWithdraw] = useState<string | null>(null);

  const activeConsents = Object.values(consents).filter((c) => c.granted);
  const expiringSoon = Object.values(consents).filter((c) => {
    if (!c.expiresAt || !c.granted) return false;
    return c.expiresAt - Date.now() < 7 * 24 * 60 * 60 * 1000;
  });

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-800">{t("auto.components.DPDPWithdrawalPanel.1")}</h3>
          <p className="text-xs text-gray-500">{t("auto.components.DPDPWithdrawalPanel.2")}</p>
        </div>
        <button
          onClick={() => setWithdrawalMode(!isWithdrawalMode)}
          className={`px-3 py-1 rounded-full text-xs font-medium transition ${
            isWithdrawalMode
              ? 'bg-red-100 text-red-700 border border-red-200'
              : 'bg-gray-100 text-gray-600 border border-gray-200'
          }`}
        >
          {isWithdrawalMode ? 'Withdrawal Mode ON' : 'Withdrawal Mode'}
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Active Consents */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {t("auto.components.DPDPWithdrawalPanel.3")}{activeConsents.length})
          </h4>
          {activeConsents.length === 0 ? (
            <p className="text-xs text-gray-400">{t("auto.components.DPDPWithdrawalPanel.4")}</p>
          ) : (
            <div className="space-y-2">
              {activeConsents.map((c) => (
                <div key={c.purpose} className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-100">
                  <div className="flex-1">
                    <div className="text-sm text-gray-800">{c.purpose}</div>
                    <div className="text-xs text-gray-500">
                      {t("auto.components.DPDPWithdrawalPanel.5")}{c.expiresAt ? new Date(c.expiresAt).toLocaleDateString('en-IN') : 'Unavailable'}
                      {expiringSoon.includes(c) && ' ⚠️'}
                    </div>
                  </div>
                  {isWithdrawalMode && (
                    <button
                      onClick={() => setConfirmWithdraw(c.purpose)}
                      className="ml-2 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition"
                    >
                      {t("auto.components.DPDPWithdrawalPanel.6")}</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Data Rights Summary */}
        <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700 space-y-1 border border-blue-100">
          <div className="font-semibold">{t("auto.components.DPDPWithdrawalPanel.7")}</div>
          <div>{t("auto.components.DPDPWithdrawalPanel.8")}</div>
          <div>{t("auto.components.DPDPWithdrawalPanel.9")}</div>
          <div>{t("auto.components.DPDPWithdrawalPanel.10")}</div>
          <div>{t("auto.components.DPDPWithdrawalPanel.11")}</div>
        </div>
      </div>

      {/* Withdrawal Confirmation Modal */}
      {confirmWithdraw && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full mx-4 overflow-hidden border border-red-200">
            <div className="px-6 py-4 bg-red-50 border-b border-red-200">
              <h3 className="text-lg font-bold text-red-800">{t("auto.components.DPDPWithdrawalPanel.12")}</h3>
            </div>
            <div className="px-6 py-4 text-sm text-gray-700">
              <p>{t("auto.components.DPDPWithdrawalPanel.13")}</p>
              <p className="font-medium mt-1 text-red-700">{confirmWithdraw}</p>
              <p className="text-xs text-gray-500 mt-2">
                {t("auto.components.DPDPWithdrawalPanel.14")}</p>
            </div>
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex gap-3">
              <button
                onClick={() => setConfirmWithdraw(null)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition text-sm"
              >
                {t("auto.components.DPDPWithdrawalPanel.15")}</button>
              <button
                onClick={() => {
                  withdrawConsent(confirmWithdraw);
                  setConfirmWithdraw(null);
                }}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
              >
                {t("auto.components.DPDPWithdrawalPanel.16")}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
