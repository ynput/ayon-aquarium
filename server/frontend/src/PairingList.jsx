import axios from 'axios'
import addonData from '/src/common'
import { useState, useEffect } from 'react'
import { Panel, ScrollPanel } from '@ynput/ayon-react-components'

import PairingButton from './PairingButton'

import styled from 'styled-components'


const PairingListPanel = styled(Panel)`
  min-width: 650px;
  max-width: 650px;
  min-height: 300px;
  max-height: 90%;
`

const Warn = styled.span`
  color: #ff6b6b;
  font-weight: bold;
`

const Table = styled.table`
  border-collapse: collapse;
  width: 100%;

  thead {
    position: sticky;
    top: 0;
    background-color: var(--md-sys-color-surface);
    border-radius: 4px;
  }

  th, td {
    padding: 0.5rem;
    height: 48px;
  }

  th {
    font-weight: bold;
    text-align: left;
  }
`




const PairingList = () => {
  const [pairings, setPairings] = useState([])

  const loadPairings = () => {
    axios
      .get(`${addonData.baseUrl}/projects/pair`)
      .then((response) => {
        setPairings(response.data)
      })
      .catch((error) => {
        //console.log(error)
      })
  }

  useEffect(() => {
    loadPairings()
  }, [])


  return (
    <PairingListPanel>
      <ScrollPanel style={{flexGrow: 1}}>
        <Table>
          <thead>
            <tr>
              <th>Aquarium project name</th>
              <th>Ayon project name</th>
              <th style={{width:1}}></th>
            </tr>
          </thead>
          <tbody>
        {pairings.map((pairing) => (
          <tr key={pairing.aquariumProjectKey}>
            <td>{pairing.aquariumProjectName}</td>
            <td>{pairing.ayonProjectName || <Warn>Not paired</Warn>}</td>
            <td><PairingButton onPair={loadPairings} pairing={pairing} /></td>
          </tr>
        ))}
          </tbody>
        </Table>
      </ScrollPanel>
    </PairingListPanel>
  )
}

export default PairingList
