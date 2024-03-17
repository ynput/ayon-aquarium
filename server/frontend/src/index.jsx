import axios from 'axios'
import addonData from '/src/common'
import React, { useContext, useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { AddonProvider, AddonContext } from '@ynput/ayon-react-addon-provider'

import PairingList from './pairing/List'

import '@ynput/ayon-react-components/dist/style.css'

import styled from 'styled-components'


const MainContainer = styled.div`
  display: grid;
  grid-template-rows: min-content 1fr;
  grid-template-columns: 1fr;
  justify-items: center;
  height: 100%;
  width: 100%;
  padding: 32px;
  gap: 32px;

  header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    width: 100%;

    h2 {
      margin: 0;
    }
  }
`



const App = () => {
  const accessToken = useContext(AddonContext).accessToken
//   const addonName = useContext(AddonContext).addonName
//   const addonVersion = useContext(AddonContext).addonVersion
  const addonName = 'aquarium' // For development
  const addonVersion = '0.0.3+git'  // For development
  const [tokenSet, setTokenSet] = useState(false)

  useEffect(() =>{
    if (addonName && addonVersion){
      addonData.addonName = addonName
      addonData.addonVersion = addonVersion
      addonData.baseUrl = `${window.location.origin}/api/addons/${addonName}/${addonVersion}`
    }

  }, [addonName, addonVersion])


  useEffect(() => {
    if (accessToken && !tokenSet) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      setTokenSet(true)
    }
  }, [accessToken, tokenSet])

  if (!tokenSet) {
    return "no token"
  }

  return <PairingList />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AddonProvider debug>
      <MainContainer>
        <header>
          <img width="200px" src="https://storage.googleapis.com/fatfishlab-public/aquarium-studio-website/aquarium-ayon-logo.min.png" alt="logo" />
          <h2>Select projects you want to pair or synchronize</h2>
        </header>
        <App />
      </MainContainer>
    </AddonProvider>
  </React.StrictMode>,
)
