package messages

type FinishBatchMsg struct {
	Agency uint8
}

func (f *FinishBatchMsg) GetType() MsgType {
	return FinishBatchMsgType
}

func (f *FinishBatchMsg) ToBytes() []byte {
	buf := make([]byte, HeaderLen+AgencyLen)

	buf[0] = uint8(f.GetType())
	buf[HeaderLen] = f.Agency
	return buf
}
