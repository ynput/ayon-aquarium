import styled from 'styled-components'
import { Panel } from '@ynput/ayon-react-components'

const Shade = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  `

  const DialogWindow = styled(Panel)`
  min-width: 30vw;
  min-height: 300px;
  padding: 32px;
  border-radius: 8px;
  border: 1px solid var(--md-sys-color-inverse-on-surface);
  box-shadow: rgb(50 72 93 / 65%) 0px 50px 100px -20px, rgba(0, 0, 0, 1) 0px 30px 60px -30px;
`


const Dialog = ({ visible, onHide, children }) => {

  if (!visible) {
    return null
  }

  const handleClose = (event) => {
    if (event.currentTarget !== event.target) return
    event.preventDefault()
    onHide()
  }

  return (
    <Shade onClick={handleClose}>
      <DialogWindow>
        {children}
      </DialogWindow>
    </Shade>
  )
}

export default Dialog
