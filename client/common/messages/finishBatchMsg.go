package messages

type FinishBatchMsg struct {
	Agency uint8
}

// GetType returns the message type identifier for FinishBatchMsg.
func (f *FinishBatchMsg) GetType() MsgType {
	return FinishBatchMsgType
}

// ToBytes serializes the FinishBatchMsg into a byte slice.
func (f *FinishBatchMsg) ToBytes() []byte {
	buf := make([]byte, HeaderLen+AgencyLen)

	buf[0] = uint8(f.GetType())
	buf[HeaderLen] = f.Agency
	return buf
}
