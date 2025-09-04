package messages

import (
	"encoding/binary"
	"fmt"
)

type WinnersMsg struct {
	Winners []string
}

const (
	WinnersMsgLen = HeaderLen
	idLen         = 4
)

func (a *WinnersMsg) GetType() MsgType {
	return WinnersMsgType
}

func WinnerMsgPayloadLen(header []byte) int {
	winnersQuantity := header[1]
	return int(winnersQuantity) * idLen
}

func BuildWinnersMsg(msg []byte) *WinnersMsg {
	if len(msg) < HeaderLen {
		return &WinnersMsg{Winners: []string{}}
	}

	winnersCount := int(msg[1])
	winners := make([]string, 0, winnersCount)

	for i := 0; i < winnersCount; i++ {
		start := HeaderLen + (i * 4)
		end := start + 4

		if end > len(msg) {
			break
		}

		id := binary.BigEndian.Uint32(msg[start:end])
		winnerID := fmt.Sprintf("%d", id)
		winners = append(winners, winnerID)
	}

	return &WinnersMsg{Winners: winners}
}
