package messages

import (
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/model"
)

type BetBatchMsg struct {
	Bets []model.Bet
}

func (b *BetBatchMsg) GetType() MsgType {
	return BetBatchMsgType
}

func (b *BetBatchMsg) ToBytes() []byte {
	payloadLen := model.TotalFixedLen * len(b.Bets)
	buf := make([]byte, HeaderLen+payloadLen)
	buf[0] = uint8(b.GetType())
	buf[1] = uint8(len(b.Bets))

	i := HeaderLen
	for _, bet := range b.Bets {
		betBytes := bet.ToBytes()
		copy(buf[i:], betBytes)
		i += model.TotalFixedLen
	}
	return buf
}
