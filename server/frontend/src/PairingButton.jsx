import axios from 'axios'
import addonData from '/src/common'

import { useState, useEffect } from 'react'

import { FormLayout, FormRow, Button, InputText } from '@ynput/ayon-react-components'
import Dialog from '/src/components/Dialog'
import styled from 'styled-components'

const DialogTitle = styled.h2`
  text-align: center;

  strong {
    color: #339af0;
    font-size: inherit;
    font-weight: inherit;
  }
`;

const ErrorContainer = styled.div`
  color: #ff6b6b;
  font-weight: bold;
  margin-top: 1rem;
  max-width: 400px;

`

const ActionButton = styled(Button)`
  width: 140px;
`


const PairingDialog = ({ pairing, onHide }) => {
  const [ayonProjectName, setAyonProjectName] = useState()
  const [ayonProjectCode, setAyonProjectCode] = useState()
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let name = pairing.aquariumProjectName
    name = name.replace(/[^a-zA-Z0-9_]/g, '_')
    name = name.replace(/_+/g, '_')
    name = name.replace(/^_/, '')
    name = name.replace(/_$/, '')
    setAyonProjectName(name)

    let code = pairing.aquariumProjectCode || pairing.aquariumProjectName
    code = code.replace(/[^a-zA-Z0-9]/g, '')
    code = code.replace(/_+/g, '')
    code = code.replace(/^_/, '')
    code = code.replace(/_$/, '')
    code = code.toLowerCase()
    code = code.substring(0, 6)
    setAyonProjectCode(code)

  }, [pairing])


  const onPair = () => {
    setLoading(true)
    axios
      .post(
        `${addonData.baseUrl}/projects/pair`, {
        aquariumProjectKey: pairing.aquariumProjectKey,
        ayonProjectName: ayonProjectName,
        ayonProjectCode: ayonProjectCode,
      })
      .then(() => {
        setError(null)
        onHide()
      })
      .catch((error) => {
        const errorMessage = error.response.data?.traceback
          || error.response.data?.detail
          || "Error on server, please check server's logs"
        setError(errorMessage)
      })
      .finally(() => {
        setLoading(false)
      })
  }

  return (
    <Dialog visible={true} onHide={onHide}>
      <DialogTitle>Pair Aquarium's project <strong>{pairing.aquariumProjectName}</strong></DialogTitle>
      <FormLayout>
        <FormRow label="Ayon project name">
          <InputText
            value={ayonProjectName}
            onChange={(e) => setAyonProjectName(e.target.value)}
          />
        </FormRow>
        <FormRow label="Ayon project code">
          <InputText
            value={ayonProjectCode}
            onChange={(e) => setAyonProjectCode(e.target.value)}
          />
        </FormRow>
        <FormRow>
          <Button label="Pair" onClick={onPair} />
        </FormRow>
      </FormLayout>
      {error && (
        <ErrorContainer>
          {error}
        </ErrorContainer>
      )}
      {loading && "Please wait..."}
    </Dialog>
  )
}


const PairingButton = ({ onPair, pairing }) => {
  const [showPairingDialog, setShowPairingDialog] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncStatus, setSyncStatus] = useState('Sync now')

  // project is not paired yet show pairing button
  if (!pairing.ayonProjectName) {
    return (
      <>
        {showPairingDialog && (
          <PairingDialog
            pairing={pairing}
            onHide={() => {
              setShowPairingDialog(false)
              onPair()
            }}
          />
        )}
        <ActionButton
          label={`Pair project`}
          icon="link"
          onClick={() => {
            setShowPairingDialog(true)
          }}
        />
      </>
    )
  }

  const onSync = () => {
    setSyncStatus('Syncing...')
    setLoading(true)
    axios
      .post(`${addonData.baseUrl}/projects/${pairing.ayonProjectName}/sync`)
      .then((response) => {
        setError(null)
        setSyncStatus('Sync triggered')
        onPair()
      })
      .catch((error) => {
        console.log(error)
        setSyncStatus('Sync error')
          console.log(error)
          console.table(error)
        setError(error.response.data?.detail || "error")

      })
      .finally(() => {
        setTimeout(() => {
          setSyncStatus('Sync now')
          setLoading(false)
          setError(null)
        }, 5000)
      })
  }

  return (
    <ActionButton
      tooltip={error}
      label={syncStatus}
      icon={loading ? (error ? 'error' : 'done') : 'sync'}
      disabled={syncStatus != 'Sync now'}
      onClick={onSync}
    />
  )

}


export default PairingButton
