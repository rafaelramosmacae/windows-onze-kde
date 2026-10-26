/*
 * Onze — tela de abertura (KSplash)
 * Fundo escuro, marca circular e o indicador de pontos giratórios.
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
import QtQuick

Rectangle {
    id: root
    color: "#101010"

    // definido pelo ksplashqml: 1..6 conforme a sessão inicia
    property int stage

    readonly property color accent: "#4CC2FF"
    readonly property real unit: Math.max(1, Math.min(width, height) / 1080)

    onStageChanged: {
        if (stage === 2) {
            intro.start()
        }
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        // Marca: anel + ponto central
        Item {
            id: mark
            width: 128 * root.unit
            height: width
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -60 * root.unit

            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: "transparent"
                border.color: root.accent
                border.width: 14 * root.unit
            }
            Rectangle {
                width: 44 * root.unit
                height: width
                radius: width / 2
                anchors.centerIn: parent
                color: root.accent
            }
        }

        // Indicador de carregamento (5 pontos em órbita)
        Item {
            id: spinner
            width: 72 * root.unit
            height: width
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: mark.bottom
            anchors.topMargin: 110 * root.unit

            Repeater {
                model: 5
                delegate: Item {
                    id: orbit
                    required property int index
                    anchors.fill: parent

                    Rectangle {
                        width: 6 * root.unit
                        height: width
                        radius: width / 2
                        color: "white"
                        x: parent.width / 2 - width / 2
                        y: 0
                    }

                    SequentialAnimation on rotation {
                        loops: Animation.Infinite
                        PauseAnimation { duration: orbit.index * 120 }
                        NumberAnimation {
                            from: 0; to: 360
                            duration: 1800
                            easing.type: Easing.InOutCubic
                        }
                        PauseAnimation { duration: (4 - orbit.index) * 120 + 200 }
                    }
                }
            }
        }
    }

    OpacityAnimator {
        id: intro
        target: content
        from: 0
        to: 1
        duration: 600
        easing.type: Easing.InOutQuad
    }

    Component.onCompleted: if (stage >= 2) content.opacity = 1
}
