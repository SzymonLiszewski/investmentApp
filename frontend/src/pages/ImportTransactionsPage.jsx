import { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import '../components/styles/ImportTransactions.css';

const STEPS = {
  BROKER: 'broker',
  UPLOAD: 'upload',
};

function ImportTransactionsPage() {
  const [step, setStep] = useState(STEPS.BROKER);
  const [selectedBroker, setSelectedBroker] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const chooseXtb = () => {
    setSelectedBroker('xtb');
    setStep(STEPS.UPLOAD);
    setError(null);
    setResult(null);
    setFile(null);
  };

  const handleFileChange = (e) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setError(null);
    setResult(null);
  };

  const submitXtb = async () => {
    if (!file) {
      setError('Please choose an .xlsx file first.');
      return;
    }
    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      setError('The file must be an Excel workbook (.xlsx).');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await apiClient.post('/api/portfolio/import/xtb/', formData, {
        transformRequest: [(data, headers) => {
          if (data instanceof FormData) {
            delete headers['Content-Type'];
          }
          return data;
        }],
      });
      setResult(res.data);
    } catch (err) {
      const msg =
        err.response?.data?.detail ??
        err.response?.data?.message ??
        err.message ??
        'Upload failed.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Fragment>
      <div className="importTxToolbar">
        <Link to="/portfolio" className="importTxBackLink">
        ← Back to portfolio
        </Link>
      </div>
      <div className="importTxCard">
        <h1 className="importTxTitle">Import transactions</h1>

        {step === STEPS.BROKER && (
          <div className="importTxSection">
            <p className="importTxLead">Choose where your transaction export comes from.</p>
            <div className="importTxBrokerGrid">
              <button
                type="button"
                className="importTxBrokerCard"
                onClick={chooseXtb}
              >
                <span className="importTxBrokerName" style={{ color: "#000" }}>XTB</span>
                <span className="importTxBrokerDesc">Excel export · Cash Operations sheet</span>
              </button>
            </div>
          </div>
        )}

        {step === STEPS.UPLOAD && selectedBroker === 'xtb' && (
          <div className="importTxSection">
            <button
              type="button"
              className="importTxGhostButton"
              onClick={() => {
                setStep(STEPS.BROKER);
                setSelectedBroker(null);
                setFile(null);
                setError(null);
                setResult(null);
              }}
            >
              ← Change broker
            </button>
            <h2 className="importTxSubtitle">XTB</h2>
            <div className="importTxInstructions">
              <p>
                Use the multi-sheet <strong>.xlsx</strong> report from XTB that includes the
                {' '}<strong>Cash Operations</strong> worksheet (cash ledger with stock and ETF trades).
              </p>
              <p>
                In xStation you can export account operations to Excel from the relevant
                reports area — the file must contain columns such as Type, Ticker, Time,
                Amount, Comment (with execution text like <code>OPEN BUY 1 @ 110.860</code>), and ID.
              </p>
              <p className="importTxHint">
                Trades we cannot parse (e.g. deposits only) are skipped automatically.
                Rows that were imported before are skipped when the same broker transaction ID is seen again.
              </p>
            </div>
            <div className="importTxUploadRow">
              <input
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={handleFileChange}
                className="importTxFileInput"
              />
            </div>
            <button
              type="button"
              className="importTxPrimaryButton"
              onClick={submitXtb}
              disabled={loading || !file}
            >
              {loading ? 'Importing…' : 'Upload and import'}
            </button>
          </div>
        )}

        {error && (
          <div className="importTxAlert importTxAlertError" role="alert">
            {error}
          </div>
        )}

        {result && (
          <div className="importTxResult">
            <p>
              <strong>{result.created_count}</strong> transaction(s) created from{' '}
              <strong>{result.parsed_row_count}</strong> parsed row(s).
            </p>
            {result.outcomes?.some((o) => o.status === 'error') && (
              <div className="importTxOutcomes">
                <p>Issues by row:</p>
                <ul>
                  {result.outcomes
                    .filter((o) => o.status === 'error')
                    .map((o, i) => (
                      <li key={`${o.source_row_index}-${i}`}>
                        Row {o.source_row_index ?? '—'}: {o.message || o.status}
                      </li>
                    ))}
                </ul>
              </div>
            )}
            {result.outcomes?.some((o) => o.status === 'skipped_duplicate') && (
              <p className="importTxMuted">
                Some rows were skipped as duplicates (already imported).
              </p>
            )}
          </div>
        )}
      </div>
    </Fragment>
  );
}

export default ImportTransactionsPage;
