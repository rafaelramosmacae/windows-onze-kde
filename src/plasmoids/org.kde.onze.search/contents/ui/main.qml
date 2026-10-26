/*
 * Onze — caixa "Search" da barra de tarefas (abre o KRunner)
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property bool iconOnly: vertical || Plasmoid.configuration.iconOnly

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.icon: "search"

    toolTipMainText: i18n("Search")
    toolTipSubText: i18n("Apps, files, settings and calculations")

    function launch() {
        executable.exec("dbus-send --session --type=method_call --dest=org.kde.krunner /App org.kde.krunner.App.display")
    }

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => disconnectSource(sourceName)
        function exec(cmd) {
            connectSource(cmd)
        }
    }

    fullRepresentation: MouseArea {
        id: area

        readonly property real pillHeight: Math.min(height - Kirigami.Units.smallSpacing * 2,
                                                    Kirigami.Units.gridUnit * 2)

        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.name: i18n("Search")
        Accessible.role: Accessible.Button

        Layout.minimumWidth: root.iconOnly ? Kirigami.Units.iconSizes.medium + Kirigami.Units.largeSpacing
                                           : Kirigami.Units.gridUnit * 11
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.minimumHeight: root.vertical ? Layout.minimumWidth : 0
        Layout.fillHeight: !root.vertical

        onClicked: root.launch()
        Keys.onReturnPressed: root.launch()
        Keys.onSpacePressed: root.launch()

        // Modo caixa (padrão)
        Rectangle {
            id: pill
            visible: !root.iconOnly
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Kirigami.Units.smallSpacing
            height: area.pillHeight
            radius: height / 2

            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false

            readonly property color fg: Kirigami.Theme.textColor
            color: area.containsMouse ? Qt.tint(Kirigami.Theme.backgroundColor, Qt.rgba(fg.r, fg.g, fg.b, 0.04))
                                      : Kirigami.Theme.backgroundColor
            border.width: 1
            border.color: area.activeFocus ? Kirigami.Theme.highlightColor
                                           : Qt.rgba(fg.r, fg.g, fg.b, 0.12)

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.largeSpacing
                anchors.rightMargin: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing * 2

                Kirigami.Icon {
                    source: "search"
                    fallback: "edit-find"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
                PlasmaComponents.Label {
                    text: i18n("Search")
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }

        // Modo somente ícone (painel vertical ou opção do usuário)
        Rectangle {
            visible: root.iconOnly && area.containsMouse
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing / 2
            radius: Kirigami.Units.cornerRadius
            readonly property color fg: Kirigami.Theme.textColor
            color: Qt.rgba(fg.r, fg.g, fg.b, area.pressed ? 0.04 : 0.06)
        }
        Kirigami.Icon {
            visible: root.iconOnly
            anchors.centerIn: parent
            width: Kirigami.Units.iconSizes.smallMedium
            height: width
            source: "search"
            fallback: "edit-find"
        }
    }
}
