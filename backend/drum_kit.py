"""The drum samples the สอนกลอง tab mixes (video-gen D11, D19, ADR 0042): three velocity
layers of ten pieces from Karoryfer Big Rusty Drums (CC0 1.0), close mics, pinned to a
commit and checked by sha256 like Kanit (`backend.fonts`, ADR 0004).

Setup fetches them, the Status check checks them, `video_gen.mixer` reads them. It sits
beside `fonts`, not in `video_gen`: setup and the Status check import it.
"""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NamedTuple

from backend import files
from backend.paths import ProjectPaths

CHECK_ID = "drum_kit"
LABEL = "Drum samples"
COMMIT = "f07ce00df34a46b6b08375be56fe116cf15782bc"
BASE_URL = f"https://raw.githubusercontent.com/sfzinstruments/karoryfer.big-rusty-drums/{COMMIT}/Samples/"
TRIES = 3

Layer = Literal["soft", "mid", "hard"]


class Sample(NamedTuple):
    """One file: a piece's velocity layer and round-robin, at `path` under the repo's `Samples/`."""

    piece: str
    layer: Layer
    round_robin: int
    path: str
    sha256: str


# Built from each piece's close-mic mapping in the repo's `Programs/mappings/` at COMMIT:
# its lowest, middle (`groups[len // 2]`) and highest velocity group, every round-robin (D19).
# The snare's close mic is `top` and the kick's `kick`: they have no `cl` folder (D26).
SAMPLES: tuple[Sample, ...] = (
    Sample("hihat_closed", "soft", 1, "hihat_14/cl/cl/ht_cl_vl1_rr1.flac", "ca4e90ed639e5cc40229b5ff9aa62483163b3686c27674eb1b12bde64d047e3a"),
    Sample("hihat_closed", "soft", 2, "hihat_14/cl/cl/ht_cl_vl1_rr2.flac", "b2c90cb06cabe5bb915e1fcff3a9c5582cd55ee0a99bdbba7227164ef1afb3e2"),
    Sample("hihat_closed", "soft", 3, "hihat_14/cl/cl/ht_cl_vl1_rr3.flac", "cdf8f653fb8a2945b7a957339b047ade5874fbef3abc0f3dd73a576ff6fd0c9f"),
    Sample("hihat_closed", "soft", 4, "hihat_14/cl/cl/ht_cl_vl1_rr4.flac", "579b81583cf5c764fe789b73d8e8df091e4710dc53ecc5b90520c25362fd76d4"),
    Sample("hihat_closed", "mid", 1, "hihat_14/cl/cl/ht_cl_vl4_rr1.flac", "df0456e6586c2cea26d16ee3dd28eaa0fd4b0d95901c2fbf00111deebf51f123"),
    Sample("hihat_closed", "mid", 2, "hihat_14/cl/cl/ht_cl_vl4_rr2.flac", "b7ebb7ffa88db92c702239ec62f57d30e47c8b9c307c0aab52f14ccafd04ef9d"),
    Sample("hihat_closed", "mid", 3, "hihat_14/cl/cl/ht_cl_vl4_rr3.flac", "7e74365fb8d1404c2b6da37939e4a43217048064e3a5fbdaee838571c950943e"),
    Sample("hihat_closed", "mid", 4, "hihat_14/cl/cl/ht_cl_vl4_rr4.flac", "ce0de3c0f32c3065055051470ad5a75431fdf71017683c3968fea0736bb32c5b"),
    Sample("hihat_closed", "hard", 1, "hihat_14/cl/cl/ht_cl_vl6_rr1.flac", "c51da9e592588bf5402627d9939521a69d5a178cd4d9dbbcc4d53e8195c60c30"),
    Sample("hihat_closed", "hard", 2, "hihat_14/cl/cl/ht_cl_vl6_rr2.flac", "8ddcb7b8a13309f75acc85982ad74f953d21629e4fc028028bfb5b6074f825b6"),
    Sample("hihat_closed", "hard", 3, "hihat_14/cl/cl/ht_cl_vl6_rr3.flac", "50276e80230b7c2543845bb25134217c002bad232708d655dec6a17c6af0c8f4"),
    Sample("hihat_closed", "hard", 4, "hihat_14/cl/cl/ht_cl_vl6_rr4.flac", "be64fe63e829e504cba8c14e951fa61a44eeb27e1116d9d85c41e18f379d4d3f"),
    Sample("hihat_open", "soft", 1, "hihat_14/open/cl/ht_open_vl1_rr1.flac", "b0d7a9594996dc156cc03801606aa9e1de1e6ab31384a61b152d6b4f952cba2e"),
    Sample("hihat_open", "soft", 2, "hihat_14/open/cl/ht_open_vl1_rr2.flac", "90ffd5affb1b4c2fa5db11672cd1d30b07eae0b48ef909bfa2f334db56f8de18"),
    Sample("hihat_open", "soft", 3, "hihat_14/open/cl/ht_open_vl1_rr3.flac", "878deb1c507bdabcdea1ab8f0b3a36245514c901ff390b9537bdbc6f8f8b0f77"),
    Sample("hihat_open", "soft", 4, "hihat_14/open/cl/ht_open_vl1_rr4.flac", "1af7e5c5ce350eaa60d3027d8deed8addec88fb3b3cc308ca9d0eaa19fdec62a"),
    Sample("hihat_open", "mid", 1, "hihat_14/open/cl/ht_open_vl4_rr1.flac", "df868a20263f218356526261f0c36251d898dc7b3b62295b72bc6cacd0aff8e9"),
    Sample("hihat_open", "mid", 2, "hihat_14/open/cl/ht_open_vl4_rr2.flac", "b66c9595e7d03f6ea9c5213f8f52b75a3cacd81f4512f8c0bce7bc85bc7ec8f5"),
    Sample("hihat_open", "mid", 3, "hihat_14/open/cl/ht_open_vl4_rr3.flac", "0db2cc96ab77b522398bd32a46290d6f7e9e05127ecf47cf5a13cf0e1023ca34"),
    Sample("hihat_open", "mid", 4, "hihat_14/open/cl/ht_open_vl4_rr4.flac", "3efc1e1c5ee14c1b341eca6dd5bba3fd2cb368562a2bbdc3c015d44cb1197e0e"),
    Sample("hihat_open", "hard", 1, "hihat_14/open/cl/ht_open_vl6_rr1.flac", "3d86d6cec08969ea5982387c624214743f2b0a6ff6630ea7fed0ffccd44d50b8"),
    Sample("hihat_open", "hard", 2, "hihat_14/open/cl/ht_open_vl6_rr2.flac", "e1ab0dc1e18876f88657a77ab95b1527838d136b3587a605b82407c053ba8881"),
    Sample("hihat_open", "hard", 3, "hihat_14/open/cl/ht_open_vl6_rr3.flac", "7960c7a73a01708a75e5ce527b4dc6c0f1b03dd0c1190555c83a3b02bfe4c1be"),
    Sample("hihat_open", "hard", 4, "hihat_14/open/cl/ht_open_vl6_rr4.flac", "fe89a420331251cfcc781ed18dcc33fe9f9933f37a6ef147eb81db9127c5e392"),
    Sample("crash", "soft", 1, "crash_17/cr/cl/cr_vl1_rr1.flac", "599f38bbe3cba2675d784ad4211ea7801c85bcb746b6b3cdfcd001db43164ac1"),
    Sample("crash", "soft", 2, "crash_17/cr/cl/cr_vl1_rr2.flac", "f519068dd9752dc7c0601a5684e9c5f83214b4eb506298421f9141011b922f38"),
    Sample("crash", "soft", 3, "crash_17/cr/cl/cr_vl1_rr3.flac", "72e3806839a5f01dad3fa70bb1fe309ff8101d0caa248e184a6597372a1dd636"),
    Sample("crash", "soft", 4, "crash_17/cr/cl/cr_vl1_rr4.flac", "4ceeb758a03f62cae0f5dc71383e8a047b64953a6c400e5213cdb9be3135f97b"),
    Sample("crash", "mid", 1, "crash_17/cr/cl/cr_vl3_rr1.flac", "051688364f5676960f1721853345ab04b4b0edbc58d399c385979c433170e35c"),
    Sample("crash", "mid", 2, "crash_17/cr/cl/cr_vl3_rr2.flac", "89ca0ea377365feffa2a8baa625481852beffed2f072c43614ee4a4281dc5cea"),
    Sample("crash", "mid", 3, "crash_17/cr/cl/cr_vl3_rr3.flac", "f8922c289d032b78f39a19d99a4fd253a8588c38cf9e33f4e2414a737923f00c"),
    Sample("crash", "mid", 4, "crash_17/cr/cl/cr_vl3_rr4.flac", "c1a505816562327087fc6a6a16f3221197b738ab8e3c16fb1d5551977cd4d69e"),
    Sample("crash", "hard", 1, "crash_17/cr/cl/cr_vl5_rr1.flac", "b9205bc10e508eec7c38f031b666bda00268ea7b68fcbc5b8a584de44ec3a1d3"),
    Sample("crash", "hard", 2, "crash_17/cr/cl/cr_vl5_rr2.flac", "a3aa2e5c2d1cbf5665ad15e95d191ce857154d673ea12278cd389b3cc070287a"),
    Sample("crash", "hard", 3, "crash_17/cr/cl/cr_vl5_rr3.flac", "975f01d13f360f6d82b7319cec33eeb5bece495833fbf87b4cdef34a3c83a872"),
    Sample("crash", "hard", 4, "crash_17/cr/cl/cr_vl5_rr4.flac", "d491b2300b66ef00f7d397058be7e65c916d826dbf52a69f3979521f8ef43233"),
    Sample("ride", "soft", 1, "ride_22/rd/cl/rd_vl1_rr1.flac", "5967648f75d21fa43e4e3b41aadc920396ef8bd1b0636dfe3cb9e19955895226"),
    Sample("ride", "soft", 2, "ride_22/rd/cl/rd_vl1_rr2.flac", "d1a8e98b0fc05f09d10bbe3926e3487eddbb5b9aad972a8974eba3921c81a777"),
    Sample("ride", "soft", 3, "ride_22/rd/cl/rd_vl1_rr3.flac", "e0fb2e54aadbc242f594f053a762b60bcb050383cc64a2f4ba919275ef42bc31"),
    Sample("ride", "mid", 1, "ride_22/rd/cl/rd_vl6_rr1.flac", "73218fa3a0f093db44e11d1b567dd014d6af2d55a8b1d581aadc7d00335fed3f"),
    Sample("ride", "mid", 2, "ride_22/rd/cl/rd_vl6_rr2.flac", "a1d26ec6df800f635bf2ca89ce300a8c033c2a8cd16db1de526805e8fc1f681f"),
    Sample("ride", "mid", 3, "ride_22/rd/cl/rd_vl6_rr3.flac", "a7851a577448bbda5994d17073a27526a4808a600f32ce3e231f5a256b348035"),
    Sample("ride", "hard", 1, "ride_22/rd/cl/rd_vl10_rr1.flac", "97be6f1be45f92919a9c932f6eed0800dc5c7e195df4b59e2e453a5cf2ed27bd"),
    Sample("ride", "hard", 2, "ride_22/rd/cl/rd_vl10_rr2.flac", "fa311598fae9669c53986d0d5ce10c569f6ee426bbf67d608359e49c3997c78c"),
    Sample("ride", "hard", 3, "ride_22/rd/cl/rd_vl10_rr3.flac", "cb07dc17c3dd9c5c38d6e540a0682fc8c836cb1650cd90596aba59facf599bf1"),
    Sample("snare", "soft", 1, "snare_14/center/top/sn_center_vl1_rr1.flac", "c1a4583d12ddc647dce96fd2286018888590d063717611e51b34bb6818e80492"),
    Sample("snare", "soft", 2, "snare_14/center/top/sn_center_vl1_rr2.flac", "e5e3754bd81b8555b687dcd170647ee55469c2142c55daec29f26140a24219e1"),
    Sample("snare", "soft", 3, "snare_14/center/top/sn_center_vl1_rr3.flac", "828fce28e5cccbea4bb6ecea77ca0bfa86ea675dbdcbdb7c2283e9a119b94c17"),
    Sample("snare", "soft", 4, "snare_14/center/top/sn_center_vl1_rr4.flac", "94b32ecf1bc5fafdb72507df5ac67c3488b2818cfea1dfa42a86ea0c065d3e2d"),
    Sample("snare", "mid", 1, "snare_14/center/top/sn_center_vl6_rr1.flac", "843f5f082b35457445ad503af80460a301bdce8aeebabe55037ae0a814afb6ad"),
    Sample("snare", "mid", 2, "snare_14/center/top/sn_center_vl6_rr2.flac", "995f94612730da329148bdb943f478e8787c59d5bb87c8be46f8792d36d44227"),
    Sample("snare", "mid", 3, "snare_14/center/top/sn_center_vl6_rr3.flac", "79f013f8a394cc3f8e12c964af247a49cdb653f590ed5b1bc5aa801f5ef7011f"),
    Sample("snare", "mid", 4, "snare_14/center/top/sn_center_vl6_rr4.flac", "8592b5e0bfda83518c7459081cbcdbab60cc5f6f0172531c5e4774d7706c2bdf"),
    Sample("snare", "hard", 1, "snare_14/center/top/sn_center_vl10_rr1.flac", "9b13c55f8804ec5d14a6a84c4f9fb47aaee2a83a546ae5b1914a8fdd858e05f5"),
    Sample("snare", "hard", 2, "snare_14/center/top/sn_center_vl10_rr2.flac", "23f971376ef0ddad37b42ac829be11e293aa89db5514873816da124f283f780a"),
    Sample("snare", "hard", 3, "snare_14/center/top/sn_center_vl10_rr3.flac", "b7c2af14aa3d546b131fcf8264cb3b86888b2dc61f3f4b91e874f09a1f7b8d79"),
    Sample("snare", "hard", 4, "snare_14/center/top/sn_center_vl10_rr4.flac", "7e8e360835047270c115bcb8c087e44f69d219af16868ca972518e4046c6b41d"),
    Sample("tom_high", "soft", 1, "tom_14/center/cl/t14_vl1_rr1.flac", "6f3c828fdd451fc0fd410f51aeef9339d56f8cbd1f1f32ab2c6f04a682c14bd5"),
    Sample("tom_high", "soft", 2, "tom_14/center/cl/t14_vl1_rr2.flac", "71593ce43195c70fabb086ba14d9eb4bc34082e7762fa995ac23c1d73a0ff292"),
    Sample("tom_high", "soft", 3, "tom_14/center/cl/t14_vl1_rr3.flac", "c41e35db4ff6bdef66649aac5ee784bcfd38374cdd2e9e72d026dfb9b8c03516"),
    Sample("tom_high", "soft", 4, "tom_14/center/cl/t14_vl1_rr4.flac", "9f1f3f7194f725d415d7719711d57cdee28934459dbee758605a19b18c882895"),
    Sample("tom_high", "mid", 1, "tom_14/center/cl/t14_vl4_rr1.flac", "d748713bdb33928c24d6c701e4432489aa7db7e9508cf1c275bc581090d5071f"),
    Sample("tom_high", "mid", 2, "tom_14/center/cl/t14_vl4_rr2.flac", "e61113b45fc817dadcedb5f211a0c459449e56d4d9c21c25a4b911441747d026"),
    Sample("tom_high", "mid", 3, "tom_14/center/cl/t14_vl4_rr3.flac", "ce2df5eb98c09f29fa3544e70e42661a3fc215a80e9f714902eb1bc355d481a8"),
    Sample("tom_high", "mid", 4, "tom_14/center/cl/t14_vl4_rr4.flac", "0915164da34dbcceddfae5fe0943c91d8c05ddbdb90dea60f914bda73a664b12"),
    Sample("tom_high", "hard", 1, "tom_14/center/cl/t14_vl6_rr1.flac", "eaf3adf05ee8a9d6bfc307608a59f13cd4991413bc18176517d6e9a00697d853"),
    Sample("tom_high", "hard", 2, "tom_14/center/cl/t14_vl6_rr2.flac", "8b2a8767bbb6a3390e921f652cbf5a0393f3bc47d9c9ff31c6b8d8f90b648fb2"),
    Sample("tom_high", "hard", 3, "tom_14/center/cl/t14_vl6_rr3.flac", "ab3f4dc5f1b812ee43750883b0ac169ae0373ccf7f5e4a66d81fa7bfeecb7230"),
    Sample("tom_high", "hard", 4, "tom_14/center/cl/t14_vl6_rr4.flac", "3b4470bff75c93ff3a1df5dc432732f6ef2fe83e10a838d832a107f42078a2c3"),
    Sample("tom_mid", "soft", 1, "tom_15/center/cl/t15_vl1_rr1.flac", "d588e506704521b93ba9c7ec1f4a58d35b71c0cda21b0c773d3ddb72eb6edc7f"),
    Sample("tom_mid", "soft", 2, "tom_15/center/cl/t15_vl1_rr2.flac", "7d909f9a90dd0aded4a6c1a52937f5fd951e3d30bc89056f0a6e938244f7a501"),
    Sample("tom_mid", "soft", 3, "tom_15/center/cl/t15_vl1_rr3.flac", "cfde45a05fdd5d3d6fcd37b9fabfa9b1dd3621861e0e49f9889b9cbadd9c1f6e"),
    Sample("tom_mid", "soft", 4, "tom_15/center/cl/t15_vl1_rr4.flac", "fafc480d4b867fc788046e684deb9af8b35937dbe9f18cba97a52f320128821c"),
    Sample("tom_mid", "mid", 1, "tom_15/center/cl/t15_vl4_rr1.flac", "48c8b595c2e25a02a6c52d4ef43fd5f3228f36a60d0911fa281d5caa7e0ca5ac"),
    Sample("tom_mid", "mid", 2, "tom_15/center/cl/t15_vl4_rr2.flac", "99bf7de3b39d1ee0b2e1b35c7ac2eaf15d6433e4137f1a2a935440ba5ae12f92"),
    Sample("tom_mid", "mid", 3, "tom_15/center/cl/t15_vl4_rr3.flac", "8ff0b12de894987ce3cc4d66dc4a7eca406e3c0cce21ebc8885060d3755e624b"),
    Sample("tom_mid", "mid", 4, "tom_15/center/cl/t15_vl4_rr4.flac", "205008323addf0c27da14228c18c8edf4c54d31bf017aacd08c65df5a439db05"),
    Sample("tom_mid", "hard", 1, "tom_15/center/cl/t15_vl7_rr1.flac", "abb1d7d04d4d1641eb0839ea908ee0bccfbdf77c62e0239bdc47ab21d83ad463"),
    Sample("tom_mid", "hard", 2, "tom_15/center/cl/t15_vl7_rr2.flac", "339558c2d2c9ec8f688dc3e5b6aefcb58d83d1765d865b4f081d973a2ac4a7b9"),
    Sample("tom_mid", "hard", 3, "tom_15/center/cl/t15_vl7_rr3.flac", "d73f0e34123722138ca5a6d3fe2b96fda197b276966e8350f839bb1962b2a4c7"),
    Sample("tom_mid", "hard", 4, "tom_15/center/cl/t15_vl7_rr4.flac", "77cd57a1fb0e906c98b6a81802860db0c8bed9418a25d2d7d083f540cc7d7ef0"),
    Sample("tom_floor", "soft", 1, "tom_18/center/cl/t18_vl1_rr1.flac", "5ce74a57f0b058a274e01369b8d4a44ed4abc1be0f1347ed7322e7f578c20efd"),
    Sample("tom_floor", "soft", 2, "tom_18/center/cl/t18_vl1_rr2.flac", "9cdb4f7e03a175abd3cc5c660edfbbb3c9535c98b5c0b1f19dcb2880cb366d34"),
    Sample("tom_floor", "soft", 3, "tom_18/center/cl/t18_vl1_rr3.flac", "96f13bcfaffa876ff988aeb12e4ea46fbd63c4f5ca803aa646ff2635cf5ddd96"),
    Sample("tom_floor", "soft", 4, "tom_18/center/cl/t18_vl1_rr4.flac", "d9e754c00248a36adc049b5c183368790e9fb61ff48ad8fccd044a8123a4f1a5"),
    Sample("tom_floor", "mid", 1, "tom_18/center/cl/t18_vl5_rr1.flac", "51cfa9aa6aec82154644a191a1a569a69d2c1deb19ebfac63b53aa11518bc07e"),
    Sample("tom_floor", "mid", 2, "tom_18/center/cl/t18_vl5_rr2.flac", "6c69a446520439e2624696a84d8d2ebb5af10c1bdfa03f02c3c4978d8f0f08d4"),
    Sample("tom_floor", "mid", 3, "tom_18/center/cl/t18_vl5_rr3.flac", "47ae1455e01d9b1aa62cc9ff3ceaceb10d16bbeb44f9df0d007fae9f521ba6c2"),
    Sample("tom_floor", "mid", 4, "tom_18/center/cl/t18_vl5_rr4.flac", "1957168cc33745b4b9c53db1db5a6d0f9eb3237b236056732a1313ea55165fe2"),
    Sample("tom_floor", "hard", 1, "tom_18/center/cl/t18_vl8_rr1.flac", "5ea672c055632d3aa3f7b9100477db64d95653960fd63985083b236b3e22ef18"),
    Sample("tom_floor", "hard", 2, "tom_18/center/cl/t18_vl8_rr2.flac", "88211caa8377c292fb4a3899d26c22ae71f9eb889d4dd520b81e26edb30ceaaf"),
    Sample("tom_floor", "hard", 3, "tom_18/center/cl/t18_vl8_rr3.flac", "8695044d6d7428f9eb2a028afe982cfa88cc3a49797c3d40be41c4fa73232418"),
    Sample("tom_floor", "hard", 4, "tom_18/center/cl/t18_vl8_rr4.flac", "bc757d732b6477bae25a65817dba5236c38244e0f25798a3d7be003053a9df2d"),
    Sample("kick", "soft", 1, "kick_24/kick/kick/k_vl1_rr1.flac", "4b1460b964f2741479eaa5654089c959442b3e73704de4ea3f820a35b9baeb4f"),
    Sample("kick", "soft", 2, "kick_24/kick/kick/k_vl1_rr2.flac", "558e42daacb401deb5bf7302bb7a6a326a270f6d1efc8d4659d511974a503a4b"),
    Sample("kick", "soft", 3, "kick_24/kick/kick/k_vl1_rr3.flac", "08e12d150b0d39090c3638d234fa336b99908c1ea4e348dabdbcd834d3e3408a"),
    Sample("kick", "soft", 4, "kick_24/kick/kick/k_vl1_rr4.flac", "d969287e2a065a8656deb6e8ab2db8bbda4b9f87ed3baf121d65925aaf57e57c"),
    Sample("kick", "mid", 1, "kick_24/kick/kick/k_vl8_rr1.flac", "6ceac70ec47243b86201889371724315336937ad5c11b2380ccad3f686ea60de"),
    Sample("kick", "mid", 2, "kick_24/kick/kick/k_vl8_rr2.flac", "3022cbddbff314116434e8d4405c5f0fb58c0dec0c0c06dbc32faa55107d3212"),
    Sample("kick", "mid", 3, "kick_24/kick/kick/k_vl8_rr3.flac", "f1d57b873097e91fa581e50214e3ab86356221c1a7fa7a58515697136c46b128"),
    Sample("kick", "mid", 4, "kick_24/kick/kick/k_vl8_rr4.flac", "b8ae313aaca5d58a2fbd4110a544e5bff070d88fbdd09bd7f880b301ff12237d"),
    Sample("kick", "hard", 1, "kick_24/kick/kick/k_vl14_rr1.flac", "3b2a6a82ab1faa9ef97f87fbc4f9dcbace81ea18149f6d7c1438da8b64f20ec3"),
    Sample("kick", "hard", 2, "kick_24/kick/kick/k_vl14_rr2.flac", "1515faafb66ff9be22a9726d0a754cc7d5d68e6cc6928f941b726795ad5585ce"),
    Sample("kick", "hard", 3, "kick_24/kick/kick/k_vl14_rr3.flac", "c2956fe4b4ae8930f75af4531d49ff0f63cf22e2d4a1bfd12e67786b294ed0f9"),
    Sample("kick", "hard", 4, "kick_24/kick/kick/k_vl14_rr4.flac", "c313f4a309b1173fc49138dd7b0ed57f7cb1305c9fb96d9037aaede650dfe803"),
    Sample("hihat_pedal", "soft", 1, "hihat_14/chik/cl/ht_chik_vl1_rr1.flac", "a69c756e2954719a9122cea8e91b2def6d9dac6e07e8c99e047c51b3e74b289e"),
    Sample("hihat_pedal", "soft", 2, "hihat_14/chik/cl/ht_chik_vl1_rr2.flac", "d22d82c7282241c804a8d01e0e0ec5d529cb0010a992a1fc8ccc72e113796323"),
    Sample("hihat_pedal", "soft", 3, "hihat_14/chik/cl/ht_chik_vl1_rr3.flac", "e36d3ac148ed8a283d734b984731df7f42bde87aa1fc291ac7d34194947e12dd"),
    Sample("hihat_pedal", "soft", 4, "hihat_14/chik/cl/ht_chik_vl1_rr4.flac", "8c6e2a1b10df438a8d636de4d62416d8802803adfaaf154362b7008bad6e34e9"),
    Sample("hihat_pedal", "mid", 1, "hihat_14/chik/cl/ht_chik_vl3_rr1.flac", "4b9d338991e950e36d6f8de26a345e6ec34c76f2e308db7daed8f60609cdddd0"),
    Sample("hihat_pedal", "mid", 2, "hihat_14/chik/cl/ht_chik_vl3_rr2.flac", "2f41883669e7e15cfb6185c3799208276361fbf7ebe06200cd59fd57c6c1f7ce"),
    Sample("hihat_pedal", "mid", 3, "hihat_14/chik/cl/ht_chik_vl3_rr3.flac", "147fceef914313a1fed18bd40454d9e870236c2c00d23f8782064527f9d12ab3"),
    Sample("hihat_pedal", "mid", 4, "hihat_14/chik/cl/ht_chik_vl3_rr4.flac", "3852a91d7383a33cc9fd9aed016d725e9867c3b57f2b6180b719e0df13d4a099"),
    Sample("hihat_pedal", "hard", 1, "hihat_14/chik/cl/ht_chik_vl5_rr1.flac", "392467ae61eb072360cd357d3aad5b37a61d8875ee5eefa5b8318b6d3a1453be"),
    Sample("hihat_pedal", "hard", 2, "hihat_14/chik/cl/ht_chik_vl5_rr2.flac", "ed351b08de8af6563c2809f2af111f3db4783625249edc9ad9b4d7453728ba1b"),
    Sample("hihat_pedal", "hard", 3, "hihat_14/chik/cl/ht_chik_vl5_rr3.flac", "253440e001e8cfcc42ee8ecfe2a162aba20cb02ed21a682dd25116e1e24ea862"),
    Sample("hihat_pedal", "hard", 4, "hihat_14/chik/cl/ht_chik_vl5_rr4.flac", "c02762737e0a6760f0903ad50d9c63f4e1a0edaceb20caeb77b7b9adac5e1571"),
)


def sample_path(project: ProjectPaths, sample: Sample) -> Path:
    return project.drum_samples_dir / sample.path


def check_drum_kit(project: ProjectPaths) -> tuple[str, str]:
    """Every file there and the marker naming the pinned sha256 of each (video-gen spec ›
    Status check and Setup). Writes nothing."""
    try:
        marker = json.loads(project.drum_kit_marker.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "missing", "ไม่พบ marker ใน models/.setup"
    except ValueError as error:
        return "missing", f"marker เสีย: {error}"
    if not isinstance(marker, dict) or marker.get("files") != _pinned():
        return "missing", "sha256 ใน marker ไม่ตรง"
    for sample in SAMPLES:
        if not sample_path(project, sample).is_file():
            return "missing", f"ไฟล์หาย: {sample.path}"
    return "ok", f"Big Rusty Drums · {COMMIT[:7]}"


def install_drum_kit(project: ProjectPaths, fetch: Callable[[str], bytes]) -> None:
    """Fetches every file that is missing or doesn't match its sha256, up to TRIES times each,
    then writes the marker last. A file that fails every try raises `RuntimeError` naming it,
    and no marker is written (spec › Status check and Setup)."""
    project.drum_kit_marker.unlink(missing_ok=True)
    for sample in SAMPLES:
        path = sample_path(project, sample)
        if path.is_file() and _sha256(path.read_bytes()) == sample.sha256:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        _fetch_checked(sample, path, fetch)
    files.write_marker(project.drum_kit_marker, _pinned())


def _fetch_checked(sample: Sample, path: Path, fetch: Callable[[str], bytes]) -> None:
    problem = ""
    for _ in range(TRIES):
        try:
            content = fetch(BASE_URL + sample.path)
        except OSError as error:
            problem = str(error)
            continue
        if _sha256(content) == sample.sha256:
            path.write_bytes(content)
            return
        problem = "sha256 ไม่ตรง"
    path.unlink(missing_ok=True)
    raise RuntimeError(f"โหลด {sample.path} ไม่สำเร็จ {TRIES} ครั้ง ({problem})")


def _pinned() -> dict[str, str]:
    return {sample.path: sample.sha256 for sample in SAMPLES}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
