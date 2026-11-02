// Global scripts 8000-8228 (a/0/5/6 entry 1241): Pearl's hidden items (arm9 table 0x20f2db4) and file 374's routine.
// Written by b2tools/pearl_items.py: do not edit. Text: a/0/0/3 file 1304.
#include "asm/field_script.inc"
#include "pearl.h"
#include "pearl_story.inc"

    ScriptEntry Hidden_0
    ScriptEntry Hidden_1
    ScriptEntry Hidden_2
    ScriptEntry Hidden_3
    ScriptEntry Hidden_4
    ScriptEntry Hidden_5
    ScriptEntry Hidden_6
    ScriptEntry Hidden_7
    ScriptEntry Hidden_8
    ScriptEntry Hidden_9
    ScriptEntry Hidden_10
    ScriptEntry Hidden_11
    ScriptEntry Hidden_12
    ScriptEntry Hidden_13
    ScriptEntry Hidden_14
    ScriptEntry Hidden_15
    ScriptEntry Hidden_16
    ScriptEntry Hidden_17
    ScriptEntry Hidden_18
    ScriptEntry Hidden_19
    ScriptEntry Hidden_20
    ScriptEntry Hidden_21
    ScriptEntry Hidden_22
    ScriptEntry Hidden_23
    ScriptEntry Hidden_24
    ScriptEntry Hidden_25
    ScriptEntry Hidden_26
    ScriptEntry Hidden_27
    ScriptEntry Hidden_28
    ScriptEntry Hidden_29
    ScriptEntry Hidden_30
    ScriptEntry Hidden_31
    ScriptEntry Hidden_32
    ScriptEntry Hidden_33
    ScriptEntry Hidden_34
    ScriptEntry Hidden_35
    ScriptEntry Hidden_36
    ScriptEntry Hidden_37
    ScriptEntry Hidden_38
    ScriptEntry Hidden_39
    ScriptEntry Hidden_40
    ScriptEntry Hidden_41
    ScriptEntry Hidden_42
    ScriptEntry Hidden_43
    ScriptEntry Hidden_44
    ScriptEntry Hidden_45
    ScriptEntry Hidden_46
    ScriptEntry Hidden_47
    ScriptEntry Hidden_48
    ScriptEntry Hidden_49
    ScriptEntry Hidden_50
    ScriptEntry Hidden_51
    ScriptEntry Hidden_52
    ScriptEntry Hidden_53
    ScriptEntry Hidden_54
    ScriptEntry Hidden_55
    ScriptEntry Hidden_56
    ScriptEntry Hidden_57
    ScriptEntry Hidden_58
    ScriptEntry Hidden_59
    ScriptEntry Hidden_60
    ScriptEntry Hidden_61
    ScriptEntry Hidden_62
    ScriptEntry Hidden_63
    ScriptEntry Hidden_64
    ScriptEntry Hidden_65
    ScriptEntry Hidden_66
    ScriptEntry Hidden_67
    ScriptEntry Hidden_68
    ScriptEntry Hidden_69
    ScriptEntry Hidden_70
    ScriptEntry Hidden_71
    ScriptEntry Hidden_72
    ScriptEntry Hidden_73
    ScriptEntry Hidden_74
    ScriptEntry Hidden_75
    ScriptEntry Hidden_76
    ScriptEntry Hidden_77
    ScriptEntry Hidden_78
    ScriptEntry Hidden_79
    ScriptEntry Hidden_80
    ScriptEntry Hidden_81
    ScriptEntry Hidden_82
    ScriptEntry Hidden_83
    ScriptEntry Hidden_84
    ScriptEntry Hidden_85
    ScriptEntry Hidden_86
    ScriptEntry Hidden_87
    ScriptEntry Hidden_88
    ScriptEntry Hidden_89
    ScriptEntry Hidden_90
    ScriptEntry Hidden_91
    ScriptEntry Hidden_92
    ScriptEntry Hidden_93
    ScriptEntry Hidden_94
    ScriptEntry Hidden_95
    ScriptEntry Hidden_96
    ScriptEntry Hidden_97
    ScriptEntry Hidden_98
    ScriptEntry Hidden_99
    ScriptEntry Hidden_100
    ScriptEntry Hidden_101
    ScriptEntry Hidden_102
    ScriptEntry Hidden_103
    ScriptEntry Hidden_104
    ScriptEntry Hidden_105
    ScriptEntry Hidden_106
    ScriptEntry Hidden_107
    ScriptEntry Hidden_108
    ScriptEntry Hidden_109
    ScriptEntry Hidden_110
    ScriptEntry Hidden_111
    ScriptEntry Hidden_112
    ScriptEntry Hidden_113
    ScriptEntry Hidden_114
    ScriptEntry Hidden_115
    ScriptEntry Hidden_116
    ScriptEntry Hidden_117
    ScriptEntry Hidden_118
    ScriptEntry Hidden_119
    ScriptEntry Hidden_120
    ScriptEntry Hidden_121
    ScriptEntry Hidden_122
    ScriptEntry Hidden_123
    ScriptEntry Hidden_124
    ScriptEntry Hidden_125
    ScriptEntry Hidden_126
    ScriptEntry Hidden_127
    ScriptEntry Hidden_128
    ScriptEntry Hidden_129
    ScriptEntry Hidden_130
    ScriptEntry Hidden_131
    ScriptEntry Hidden_132
    ScriptEntry Hidden_133
    ScriptEntry Hidden_134
    ScriptEntry Hidden_135
    ScriptEntry Hidden_136
    ScriptEntry Hidden_137
    ScriptEntry Hidden_138
    ScriptEntry Hidden_139
    ScriptEntry Hidden_140
    ScriptEntry Hidden_141
    ScriptEntry Hidden_142
    ScriptEntry Hidden_143
    ScriptEntry Hidden_144
    ScriptEntry Hidden_145
    ScriptEntry Hidden_146
    ScriptEntry Hidden_147
    ScriptEntry Hidden_148
    ScriptEntry Hidden_149
    ScriptEntry Hidden_150
    ScriptEntry Hidden_151
    ScriptEntry Hidden_152
    ScriptEntry Hidden_153
    ScriptEntry Hidden_154
    ScriptEntry Hidden_155
    ScriptEntry Hidden_156
    ScriptEntry Hidden_157
    ScriptEntry Hidden_158
    ScriptEntry Hidden_159
    ScriptEntry Hidden_160
    ScriptEntry Hidden_161
    ScriptEntry Hidden_162
    ScriptEntry Hidden_163
    ScriptEntry Hidden_164
    ScriptEntry Hidden_165
    ScriptEntry Hidden_166
    ScriptEntry Hidden_167
    ScriptEntry Hidden_168
    ScriptEntry Hidden_169
    ScriptEntry Hidden_170
    ScriptEntry Hidden_171
    ScriptEntry Hidden_172
    ScriptEntry Hidden_173
    ScriptEntry Hidden_174
    ScriptEntry Hidden_175
    ScriptEntry Hidden_176
    ScriptEntry Hidden_177
    ScriptEntry Hidden_178
    ScriptEntry Hidden_179
    ScriptEntry Hidden_180
    ScriptEntry Hidden_181
    ScriptEntry Hidden_182
    ScriptEntry Hidden_183
    ScriptEntry Hidden_184
    ScriptEntry Hidden_185
    ScriptEntry Hidden_186
    ScriptEntry Hidden_187
    ScriptEntry Hidden_188
    ScriptEntry Hidden_189
    ScriptEntry Hidden_190
    ScriptEntry Hidden_191
    ScriptEntry Hidden_192
    ScriptEntry Hidden_193
    ScriptEntry Hidden_194
    ScriptEntry Hidden_195
    ScriptEntry Hidden_196
    ScriptEntry Hidden_197
    ScriptEntry Hidden_198
    ScriptEntry Hidden_199
    ScriptEntry Hidden_200
    ScriptEntry Hidden_201
    ScriptEntry Hidden_202
    ScriptEntry Hidden_203
    ScriptEntry Hidden_204
    ScriptEntry Hidden_205
    ScriptEntry Hidden_206
    ScriptEntry Hidden_207
    ScriptEntry Hidden_208
    ScriptEntry Hidden_209
    ScriptEntry Hidden_210
    ScriptEntry Hidden_211
    ScriptEntry Hidden_212
    ScriptEntry Hidden_213
    ScriptEntry Hidden_214
    ScriptEntry Hidden_215
    ScriptEntry Hidden_216
    ScriptEntry Hidden_217
    ScriptEntry Hidden_218
    ScriptEntry Hidden_219
    ScriptEntry Hidden_220
    ScriptEntry Hidden_221
    ScriptEntry Hidden_222
    ScriptEntry Hidden_223
    ScriptEntry Hidden_224
    ScriptEntry Hidden_225
    ScriptEntry Hidden_226
    ScriptEntry Hidden_227
    ScriptEntry Hidden_228
    ScriptEntriesEnd

Hidden_0:   // Pearl script 8000: 1 of item 41, range 1
    WorkSet PVAR_8000, 41
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2820
    VMJump H_Start

Hidden_1:   // Pearl script 8001: 1 of item 308, range 1
    WorkSet PVAR_8000, 308
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2821
    VMJump H_Start

Hidden_2:   // Pearl script 8002: 1 of item 311, range 1
    WorkSet PVAR_8000, 311
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2822
    VMJump H_Start

Hidden_3:   // Pearl script 8003: 1 of item 4, range 1
    WorkSet PVAR_8000, 4
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2823
    VMJump H_Start

Hidden_4:   // Pearl script 8004: 1 of item 40, range 2
    WorkSet PVAR_8000, 40
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2824
    VMJump H_Start

Hidden_5:   // Pearl script 8005: 1 of item 17, range 2
    WorkSet PVAR_8000, 17
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2825
    VMJump H_Start

Hidden_6:   // Pearl script 8006: 1 of item 92, range 2
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2826
    VMJump H_Start

Hidden_7:   // Pearl script 8007: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2827
    VMJump H_Start

Hidden_8:   // Pearl script 8008: 1 of item 26, range 2
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2828
    VMJump H_Start

Hidden_9:   // Pearl script 8009: 1 of item 19, range 2
    WorkSet PVAR_8000, 19
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2829
    VMJump H_Start

Hidden_10:   // Pearl script 8010: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2830
    VMJump H_Start

Hidden_11:   // Pearl script 8011: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2831
    VMJump H_Start

Hidden_12:   // Pearl script 8012: 1 of item 50, range 2
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2832
    VMJump H_Start

Hidden_13:   // Pearl script 8013: 1 of item 38, range 1
    WorkSet PVAR_8000, 38
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2833
    VMJump H_Start

Hidden_14:   // Pearl script 8014: 1 of item 47, range 1
    WorkSet PVAR_8000, 47
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2834
    VMJump H_Start

Hidden_15:   // Pearl script 8015: 1 of item 94, range 2
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2835
    VMJump H_Start

Hidden_16:   // Pearl script 8016: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2836
    VMJump H_Start

Hidden_17:   // Pearl script 8017: 1 of item 26, range 1
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2837
    VMJump H_Start

Hidden_18:   // Pearl script 8018: 1 of item 3, range 1
    WorkSet PVAR_8000, 3
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2838
    VMJump H_Start

Hidden_19:   // Pearl script 8019: 1 of item 46, range 1
    WorkSet PVAR_8000, 46
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2839
    VMJump H_Start

Hidden_20:   // Pearl script 8020: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2840
    VMJump H_Start

Hidden_21:   // Pearl script 8021: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2841
    VMJump H_Start

Hidden_22:   // Pearl script 8022: 1 of item 38, range 1
    WorkSet PVAR_8000, 38
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2842
    VMJump H_Start

Hidden_23:   // Pearl script 8023: 1 of item 93, range 1
    WorkSet PVAR_8000, 93
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2843
    VMJump H_Start

Hidden_24:   // Pearl script 8024: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2844
    VMJump H_Start

Hidden_25:   // Pearl script 8025: 1 of item 3, range 1
    WorkSet PVAR_8000, 3
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2845
    VMJump H_Start

Hidden_26:   // Pearl script 8026: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2846
    VMJump H_Start

Hidden_27:   // Pearl script 8027: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2847
    VMJump H_Start

Hidden_28:   // Pearl script 8028: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2848
    VMJump H_Start

Hidden_29:   // Pearl script 8029: 1 of item 89, range 1
    WorkSet PVAR_8000, 89
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2849
    VMJump H_Start

Hidden_30:   // Pearl script 8030: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2850
    VMJump H_Start

Hidden_31:   // Pearl script 8031: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2851
    VMJump H_Start

Hidden_32:   // Pearl script 8032: 1 of item 21, range 1
    WorkSet PVAR_8000, 21
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2852
    VMJump H_Start

Hidden_33:   // Pearl script 8033: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2853
    VMJump H_Start

Hidden_34:   // Pearl script 8034: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2854
    VMJump H_Start

Hidden_35:   // Pearl script 8035: 1 of item 26, range 1
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2855
    VMJump H_Start

Hidden_36:   // Pearl script 8036: 1 of item 79, range 1
    WorkSet PVAR_8000, 79
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2856
    VMJump H_Start

Hidden_37:   // Pearl script 8037: 1 of item 78, range 1
    WorkSet PVAR_8000, 78
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2857
    VMJump H_Start

Hidden_38:   // Pearl script 8038: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2858
    VMJump H_Start

Hidden_39:   // Pearl script 8039: 1 of item 38, range 1
    WorkSet PVAR_8000, 38
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2859
    VMJump H_Start

Hidden_40:   // Pearl script 8040: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2860
    VMJump H_Start

Hidden_41:   // Pearl script 8041: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2861
    VMJump H_Start

Hidden_42:   // Pearl script 8042: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2862
    VMJump H_Start

Hidden_43:   // Pearl script 8043: 1 of item 93, range 1
    WorkSet PVAR_8000, 93
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2863
    VMJump H_Start

Hidden_44:   // Pearl script 8044: 1 of item 301, range 1
    WorkSet PVAR_8000, 301
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2864
    VMJump H_Start

Hidden_45:   // Pearl script 8045: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2865
    VMJump H_Start

Hidden_46:   // Pearl script 8046: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2866
    VMJump H_Start

Hidden_47:   // Pearl script 8047: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2867
    VMJump H_Start

Hidden_48:   // Pearl script 8048: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2868
    VMJump H_Start

Hidden_49:   // Pearl script 8049: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2869
    VMJump H_Start

Hidden_50:   // Pearl script 8050: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2870
    VMJump H_Start

Hidden_51:   // Pearl script 8051: 1 of item 39, range 1
    WorkSet PVAR_8000, 39
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2871
    VMJump H_Start

Hidden_52:   // Pearl script 8052: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2872
    VMJump H_Start

Hidden_53:   // Pearl script 8053: 1 of item 47, range 1
    WorkSet PVAR_8000, 47
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2873
    VMJump H_Start

Hidden_54:   // Pearl script 8054: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2874
    VMJump H_Start

Hidden_55:   // Pearl script 8055: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2875
    VMJump H_Start

Hidden_56:   // Pearl script 8056: 1 of item 313, range 1
    WorkSet PVAR_8000, 313
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2876
    VMJump H_Start

Hidden_57:   // Pearl script 8057: 1 of item 45, range 1
    WorkSet PVAR_8000, 45
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2877
    VMJump H_Start

Hidden_58:   // Pearl script 8058: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2878
    VMJump H_Start

Hidden_59:   // Pearl script 8059: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2879
    VMJump H_Start

Hidden_60:   // Pearl script 8060: 1 of item 52, range 1
    WorkSet PVAR_8000, 52
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2880
    VMJump H_Start

Hidden_61:   // Pearl script 8061: 1 of item 45, range 1
    WorkSet PVAR_8000, 45
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2881
    VMJump H_Start

Hidden_62:   // Pearl script 8062: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2882
    VMJump H_Start

Hidden_63:   // Pearl script 8063: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2883
    VMJump H_Start

Hidden_64:   // Pearl script 8064: 1 of item 40, range 1
    WorkSet PVAR_8000, 40
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2884
    VMJump H_Start

Hidden_65:   // Pearl script 8065: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2885
    VMJump H_Start

Hidden_66:   // Pearl script 8066: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2886
    VMJump H_Start

Hidden_67:   // Pearl script 8067: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2887
    VMJump H_Start

Hidden_68:   // Pearl script 8068: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2888
    VMJump H_Start

Hidden_69:   // Pearl script 8069: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2889
    VMJump H_Start

Hidden_70:   // Pearl script 8070: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2890
    VMJump H_Start

Hidden_71:   // Pearl script 8071: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2891
    VMJump H_Start

Hidden_72:   // Pearl script 8072: 1 of item 49, range 1
    WorkSet PVAR_8000, 49
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2892
    VMJump H_Start

Hidden_73:   // Pearl script 8073: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2893
    VMJump H_Start

Hidden_74:   // Pearl script 8074: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2894
    VMJump H_Start

Hidden_75:   // Pearl script 8075: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2895
    VMJump H_Start

Hidden_76:   // Pearl script 8076: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2896
    VMJump H_Start

Hidden_77:   // Pearl script 8077: 1 of item 40, range 1
    WorkSet PVAR_8000, 40
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2897
    VMJump H_Start

Hidden_78:   // Pearl script 8078: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2898
    VMJump H_Start

Hidden_79:   // Pearl script 8079: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2899
    VMJump H_Start

Hidden_80:   // Pearl script 8080: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2900
    VMJump H_Start

Hidden_81:   // Pearl script 8081: 1 of item 38, range 1
    WorkSet PVAR_8000, 38
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2901
    VMJump H_Start

Hidden_82:   // Pearl script 8082: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2902
    VMJump H_Start

Hidden_83:   // Pearl script 8083: 1 of item 76, range 1
    WorkSet PVAR_8000, 76
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2903
    VMJump H_Start

Hidden_84:   // Pearl script 8084: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2904
    VMJump H_Start

Hidden_85:   // Pearl script 8085: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2905
    VMJump H_Start

Hidden_86:   // Pearl script 8086: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2906
    VMJump H_Start

Hidden_87:   // Pearl script 8087: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2907
    VMJump H_Start

Hidden_88:   // Pearl script 8088: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2908
    VMJump H_Start

Hidden_89:   // Pearl script 8089: 1 of item 24, range 1
    WorkSet PVAR_8000, 24
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2909
    VMJump H_Start

Hidden_90:   // Pearl script 8090: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2910
    VMJump H_Start

Hidden_91:   // Pearl script 8091: 1 of item 4, range 2
    WorkSet PVAR_8000, 4
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2911
    VMJump H_Start

Hidden_92:   // Pearl script 8092: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2912
    VMJump H_Start

Hidden_93:   // Pearl script 8093: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2913
    VMJump H_Start

Hidden_94:   // Pearl script 8094: 1 of item 38, range 1
    WorkSet PVAR_8000, 38
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2914
    VMJump H_Start

Hidden_95:   // Pearl script 8095: 1 of item 78, range 1
    WorkSet PVAR_8000, 78
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2915
    VMJump H_Start

Hidden_96:   // Pearl script 8096: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2916
    VMJump H_Start

Hidden_97:   // Pearl script 8097: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2917
    VMJump H_Start

Hidden_98:   // Pearl script 8098: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2918
    VMJump H_Start

Hidden_99:   // Pearl script 8099: 1 of item 309, range 1
    WorkSet PVAR_8000, 309
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2919
    VMJump H_Start

Hidden_100:   // Pearl script 8100: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2920
    VMJump H_Start

Hidden_101:   // Pearl script 8101: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2921
    VMJump H_Start

Hidden_102:   // Pearl script 8102: 1 of item 24, range 1
    WorkSet PVAR_8000, 24
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2922
    VMJump H_Start

Hidden_103:   // Pearl script 8103: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2923
    VMJump H_Start

Hidden_104:   // Pearl script 8104: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2924
    VMJump H_Start

Hidden_105:   // Pearl script 8105: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2925
    VMJump H_Start

Hidden_106:   // Pearl script 8106: 1 of item 39, range 1
    WorkSet PVAR_8000, 39
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2926
    VMJump H_Start

Hidden_107:   // Pearl script 8107: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2927
    VMJump H_Start

Hidden_108:   // Pearl script 8108: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2928
    VMJump H_Start

Hidden_109:   // Pearl script 8109: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2929
    VMJump H_Start

Hidden_110:   // Pearl script 8110: 1 of item 300, range 1
    WorkSet PVAR_8000, 300
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2930
    VMJump H_Start

Hidden_111:   // Pearl script 8111: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2931
    VMJump H_Start

Hidden_112:   // Pearl script 8112: 1 of item 89, range 1
    WorkSet PVAR_8000, 89
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2932
    VMJump H_Start

Hidden_113:   // Pearl script 8113: 1 of item 41, range 1
    WorkSet PVAR_8000, 41
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2933
    VMJump H_Start

Hidden_114:   // Pearl script 8114: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2934
    VMJump H_Start

Hidden_115:   // Pearl script 8115: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2935
    VMJump H_Start

Hidden_116:   // Pearl script 8116: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2936
    VMJump H_Start

Hidden_117:   // Pearl script 8117: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2937
    VMJump H_Start

Hidden_118:   // Pearl script 8118: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2938
    VMJump H_Start

Hidden_119:   // Pearl script 8119: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2939
    VMJump H_Start

Hidden_120:   // Pearl script 8120: 1 of item 306, range 1
    WorkSet PVAR_8000, 306
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2940
    VMJump H_Start

Hidden_121:   // Pearl script 8121: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2941
    VMJump H_Start

Hidden_122:   // Pearl script 8122: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2942
    VMJump H_Start

Hidden_123:   // Pearl script 8123: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2943
    VMJump H_Start

Hidden_124:   // Pearl script 8124: 1 of item 53, range 0
    WorkSet PVAR_8000, 53
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2944
    VMJump H_Start

Hidden_125:   // Pearl script 8125: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2945
    VMJump H_Start

Hidden_126:   // Pearl script 8126: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2946
    VMJump H_Start

Hidden_127:   // Pearl script 8127: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2947
    VMJump H_Start

Hidden_128:   // Pearl script 8128: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2948
    VMJump H_Start

Hidden_129:   // Pearl script 8129: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2949
    VMJump H_Start

Hidden_130:   // Pearl script 8130: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2950
    VMJump H_Start

Hidden_131:   // Pearl script 8131: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2951
    VMJump H_Start

Hidden_132:   // Pearl script 8132: 1 of item 87, range 0
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2952
    VMJump H_Start

Hidden_133:   // Pearl script 8133: 1 of item 86, range 0
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2953
    VMJump H_Start

Hidden_134:   // Pearl script 8134: 1 of item 86, range 0
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2954
    VMJump H_Start

Hidden_135:   // Pearl script 8135: 1 of item 89, range 1
    WorkSet PVAR_8000, 89
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2955
    VMJump H_Start

Hidden_136:   // Pearl script 8136: 1 of item 46, range 1
    WorkSet PVAR_8000, 46
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2956
    VMJump H_Start

Hidden_137:   // Pearl script 8137: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2957
    VMJump H_Start

Hidden_138:   // Pearl script 8138: 1 of item 41, range 1
    WorkSet PVAR_8000, 41
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2958
    VMJump H_Start

Hidden_139:   // Pearl script 8139: 1 of item 298, range 1
    WorkSet PVAR_8000, 298
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2959
    VMJump H_Start

Hidden_140:   // Pearl script 8140: 1 of item 52, range 1
    WorkSet PVAR_8000, 52
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2960
    VMJump H_Start

Hidden_141:   // Pearl script 8141: 1 of item 47, range 1
    WorkSet PVAR_8000, 47
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2961
    VMJump H_Start

Hidden_142:   // Pearl script 8142: 1 of item 49, range 1
    WorkSet PVAR_8000, 49
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2962
    VMJump H_Start

Hidden_143:   // Pearl script 8143: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2963
    VMJump H_Start

Hidden_144:   // Pearl script 8144: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2964
    VMJump H_Start

Hidden_145:   // Pearl script 8145: 1 of item 87, range 1
    WorkSet PVAR_8000, 87
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2965
    VMJump H_Start

Hidden_146:   // Pearl script 8146: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2966
    VMJump H_Start

Hidden_147:   // Pearl script 8147: 1 of item 48, range 1
    WorkSet PVAR_8000, 48
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2967
    VMJump H_Start

Hidden_148:   // Pearl script 8148: 1 of item 45, range 1
    WorkSet PVAR_8000, 45
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2968
    VMJump H_Start

Hidden_149:   // Pearl script 8149: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2969
    VMJump H_Start

Hidden_150:   // Pearl script 8150: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2970
    VMJump H_Start

Hidden_151:   // Pearl script 8151: 1 of item 28, range 2
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2971
    VMJump H_Start

Hidden_152:   // Pearl script 8152: 1 of item 21, range 1
    WorkSet PVAR_8000, 21
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2972
    VMJump H_Start

Hidden_153:   // Pearl script 8153: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2973
    VMJump H_Start

Hidden_154:   // Pearl script 8154: 1 of item 3, range 1
    WorkSet PVAR_8000, 3
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2974
    VMJump H_Start

Hidden_155:   // Pearl script 8155: 1 of item 24, range 1
    WorkSet PVAR_8000, 24
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2975
    VMJump H_Start

Hidden_156:   // Pearl script 8156: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2976
    VMJump H_Start

Hidden_157:   // Pearl script 8157: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2977
    VMJump H_Start

Hidden_158:   // Pearl script 8158: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2978
    VMJump H_Start

Hidden_159:   // Pearl script 8159: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2979
    VMJump H_Start

Hidden_160:   // Pearl script 8160: 1 of item 17, range 1
    WorkSet PVAR_8000, 17
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2980
    VMJump H_Start

Hidden_161:   // Pearl script 8161: 1 of item 22, range 1
    WorkSet PVAR_8000, 22
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2981
    VMJump H_Start

Hidden_162:   // Pearl script 8162: 1 of item 17, range 2
    WorkSet PVAR_8000, 17
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2982
    VMJump H_Start

Hidden_163:   // Pearl script 8163: 1 of item 19, range 1
    WorkSet PVAR_8000, 19
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2983
    VMJump H_Start

Hidden_164:   // Pearl script 8164: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2984
    VMJump H_Start

Hidden_165:   // Pearl script 8165: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2985
    VMJump H_Start

Hidden_166:   // Pearl script 8166: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2986
    VMJump H_Start

Hidden_167:   // Pearl script 8167: 1 of item 18, range 1
    WorkSet PVAR_8000, 18
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2987
    VMJump H_Start

Hidden_168:   // Pearl script 8168: 1 of item 86, range 1
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2988
    VMJump H_Start

Hidden_169:   // Pearl script 8169: 1 of item 26, range 1
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2989
    VMJump H_Start

Hidden_170:   // Pearl script 8170: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2990
    VMJump H_Start

Hidden_171:   // Pearl script 8171: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2991
    VMJump H_Start

Hidden_172:   // Pearl script 8172: 1 of item 89, range 1
    WorkSet PVAR_8000, 89
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2992
    VMJump H_Start

Hidden_173:   // Pearl script 8173: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2993
    VMJump H_Start

Hidden_174:   // Pearl script 8174: 1 of item 29, range 1
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2994
    VMJump H_Start

Hidden_175:   // Pearl script 8175: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2995
    VMJump H_Start

Hidden_176:   // Pearl script 8176: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2996
    VMJump H_Start

Hidden_177:   // Pearl script 8177: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2997
    VMJump H_Start

Hidden_178:   // Pearl script 8178: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2998
    VMJump H_Start

Hidden_179:   // Pearl script 8179: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 2999
    VMJump H_Start

Hidden_180:   // Pearl script 8180: 1 of item 39, range 1
    WorkSet PVAR_8000, 39
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3000
    VMJump H_Start

Hidden_181:   // Pearl script 8181: 1 of item 94, range 1
    WorkSet PVAR_8000, 94
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3001
    VMJump H_Start

Hidden_182:   // Pearl script 8182: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3002
    VMJump H_Start

Hidden_183:   // Pearl script 8183: 1 of item 52, range 1
    WorkSet PVAR_8000, 52
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3003
    VMJump H_Start

Hidden_184:   // Pearl script 8184: 1 of item 3, range 1
    WorkSet PVAR_8000, 3
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3004
    VMJump H_Start

Hidden_185:   // Pearl script 8185: 1 of item 49, range 1
    WorkSet PVAR_8000, 49
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3005
    VMJump H_Start

Hidden_186:   // Pearl script 8186: 1 of item 26, range 1
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3006
    VMJump H_Start

Hidden_187:   // Pearl script 8187: 1 of item 90, range 1
    WorkSet PVAR_8000, 90
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3007
    VMJump H_Start

Hidden_188:   // Pearl script 8188: 1 of item 3, range 1
    WorkSet PVAR_8000, 3
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3008
    VMJump H_Start

Hidden_189:   // Pearl script 8189: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3009
    VMJump H_Start

Hidden_190:   // Pearl script 8190: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3010
    VMJump H_Start

Hidden_191:   // Pearl script 8191: 1 of item 48, range 1
    WorkSet PVAR_8000, 48
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3011
    VMJump H_Start

Hidden_192:   // Pearl script 8192: 1 of item 29, range 0
    WorkSet PVAR_8000, 29
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3012
    VMJump H_Start

Hidden_193:   // Pearl script 8193: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3013
    VMJump H_Start

Hidden_194:   // Pearl script 8194: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3014
    VMJump H_Start

Hidden_195:   // Pearl script 8195: 1 of item 77, range 1
    WorkSet PVAR_8000, 77
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3015
    VMJump H_Start

Hidden_196:   // Pearl script 8196: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3016
    VMJump H_Start

Hidden_197:   // Pearl script 8197: 1 of item 46, range 1
    WorkSet PVAR_8000, 46
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3017
    VMJump H_Start

Hidden_198:   // Pearl script 8198: 1 of item 24, range 1
    WorkSet PVAR_8000, 24
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3018
    VMJump H_Start

Hidden_199:   // Pearl script 8199: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3019
    VMJump H_Start

Hidden_200:   // Pearl script 8200: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3020
    VMJump H_Start

Hidden_201:   // Pearl script 8201: 1 of item 111, range 0
    WorkSet PVAR_8000, 111
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3021
    VMJump H_Start

Hidden_202:   // Pearl script 8202: 1 of item 19, range 1
    WorkSet PVAR_8000, 19
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3022
    VMJump H_Start

Hidden_203:   // Pearl script 8203: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3023
    VMJump H_Start

Hidden_204:   // Pearl script 8204: 1 of item 77, range 1
    WorkSet PVAR_8000, 77
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3024
    VMJump H_Start

Hidden_205:   // Pearl script 8205: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3025
    VMJump H_Start

Hidden_206:   // Pearl script 8206: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3026
    VMJump H_Start

Hidden_207:   // Pearl script 8207: 1 of item 23, range 1
    WorkSet PVAR_8000, 23
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3027
    VMJump H_Start

Hidden_208:   // Pearl script 8208: 1 of item 17, range 2
    WorkSet PVAR_8000, 17
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3028
    VMJump H_Start

Hidden_209:   // Pearl script 8209: 1 of item 86, range 2
    WorkSet PVAR_8000, 86
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3029
    VMJump H_Start

Hidden_210:   // Pearl script 8210: 1 of item 50, range 1
    WorkSet PVAR_8000, 50
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3030
    VMJump H_Start

Hidden_211:   // Pearl script 8211: 1 of item 304, range 1
    WorkSet PVAR_8000, 304
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3031
    VMJump H_Start

Hidden_212:   // Pearl script 8212: 1 of item 2, range 1
    WorkSet PVAR_8000, 2
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3032
    VMJump H_Start

Hidden_213:   // Pearl script 8213: 1 of item 92, range 1
    WorkSet PVAR_8000, 92
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3033
    VMJump H_Start

Hidden_214:   // Pearl script 8214: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3034
    VMJump H_Start

Hidden_215:   // Pearl script 8215: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3035
    VMJump H_Start

Hidden_216:   // Pearl script 8216: 1 of item 451, range 0
    WorkSet PVAR_8000, 451
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3036
    VMJump H_Start

Hidden_217:   // Pearl script 8217: 1 of item 18, range 1
    WorkSet PVAR_8000, 18
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3037
    VMJump H_Start

Hidden_218:   // Pearl script 8218: 1 of item 88, range 1
    WorkSet PVAR_8000, 88
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3038
    VMJump H_Start

Hidden_219:   // Pearl script 8219: 1 of item 25, range 1
    WorkSet PVAR_8000, 25
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3039
    VMJump H_Start

Hidden_220:   // Pearl script 8220: 1 of item 27, range 1
    WorkSet PVAR_8000, 27
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3040
    VMJump H_Start

Hidden_221:   // Pearl script 8221: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3041
    VMJump H_Start

Hidden_222:   // Pearl script 8222: 1 of item 18, range 1
    WorkSet PVAR_8000, 18
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3042
    VMJump H_Start

Hidden_223:   // Pearl script 8223: 1 of item 26, range 1
    WorkSet PVAR_8000, 26
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3043
    VMJump H_Start

Hidden_224:   // Pearl script 8224: 1 of item 22, range 1
    WorkSet PVAR_8000, 22
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3044
    VMJump H_Start

Hidden_225:   // Pearl script 8225: 1 of item 17, range 1
    WorkSet PVAR_8000, 17
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3045
    VMJump H_Start

Hidden_226:   // Pearl script 8226: 1 of item 24, range 1
    WorkSet PVAR_8000, 24
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3046
    VMJump H_Start

Hidden_227:   // Pearl script 8227: 1 of item 28, range 1
    WorkSet PVAR_8000, 28
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3047
    VMJump H_Start

Hidden_228:   // Pearl script 8228: 1 of item 51, range 1
    WorkSet PVAR_8000, 51
    WorkSet PVAR_8001, 1
    WorkSet PVAR_8002, 3048
    VMJump H_Start

H_Start:
    ActorsPauseAll
    pl_PlaySE SEQ_SE_MESSAGE
    VMCall H_Find
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

H_Find:
H_0402:
    pl_WaitSE SEQ_SE_MESSAGE  // Pearl SEQ_SE_DP_SELECT
    pl_SetVarFromVar PVAR_8004, PVAR_8000
    pl_SetVarFromVar PVAR_8005, PVAR_8001
    pl_SetVarFromVar PVAR_8006, PVAR_8002
    pl_CanFitItem PVAR_8004, PVAR_8005, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, H_0440
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, H_05DF
    VMReturn  // End: the sub-script ends

H_043C:
    pl_CloseMessage
    VMReturn  // End: the sub-script ends

H_0440:
    VMCall C205_2_S2  // CallCommonScript 2001 (Pearl file 205 script 2)
    RecordAdd 44, 1  // SaveTVSegmentHiddenItem: Black 2's record of hidden items found
    pl_AddItem PVAR_8004, PVAR_8005, PVAR_800C
    ItemIsTMHM PVAR_8004, PVAR_800C  // ItemIdIsTMOrHM
    pl_CompareVarToValue PVAR_800C, 1
    pl_GoToIf 1, H_05B4
    pl_CompareVarToValue PVAR_800C, 0
    pl_GoToIf 1, H_05CC
    VMReturn  // End: the sub-script ends

H_0472:
    pl_WaitFanfare
    pl_CheckItemIsPlate PVAR_8004, PVAR_800C
    pl_CompareVarToValue PVAR_800C, 1
    pl_CallIf 1, H_05F7
    pl_BufferPlayerName 0
    pl_BufferItemName 1, PVAR_8004
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 7
    pl_GoToIf 1, H_0518
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, H_0505
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, H_0564
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, H_0551
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, H_0577
    pl_CompareVarToValue PVAR_8008, 6
    pl_GoToIf 1, H_058A
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, H_053E
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, H_052B
    VMReturn  // End: the sub-script ends

H_0505:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_0518:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_052B:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_053E:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_0551:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_0564:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_0577:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_058A:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_BufferPocketName 2, PVAR_800C
    pl_GoTo H_059D

H_059D:
    pl_SetFlagFromVar PVAR_8006
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 9  // Pearl bank 333 line 9
    pl_WaitButton
    pl_SetVarFromValue PVAR_800C, 1
    pl_GoTo H_043C

H_05B4:
    pl_BufferPlayerName 0
    WordSetItemNameWithArticle 1, PVAR_8004
    pl_BufferTMHMMoveName 2, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 6  // Pearl bank 333 line 6
    pl_GoTo H_0472

H_05CC:
    pl_BufferPlayerName 0
    WordSetItemNameWithArticle 1, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 3  // Pearl bank 333 line 3
    pl_GoTo H_0472

H_05DF:
    pl_BufferItemName 0, PVAR_8004
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 4  // Pearl bank 333 line 4
    pl_WaitButton
    pl_SetVarFromValue PVAR_800C, 0
    pl_GoTo H_043C

H_05F7:
    VMCall C205_39_S39  // CallCommonScript 2038 (Pearl file 205 script 39)
    pl_Return

// ---- Pearl global script 205:2 (a subroutine here)
C205_2_S2:
C205_2_032C:
    pl_Call C205_2_0336
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_2_0336:
    pl_GetItemPocket PVAR_8004, PVAR_800C
    pl_SetVarFromVar PVAR_8008, PVAR_800C
    pl_CompareVarToValue PVAR_8008, 7
    pl_GoToIf 1, C205_2_03B8
    pl_CompareVarToValue PVAR_8008, 0
    pl_GoToIf 1, C205_2_03AC
    pl_CompareVarToValue PVAR_8008, 4
    pl_GoToIf 1, C205_2_03AC
    pl_CompareVarToValue PVAR_8008, 1
    pl_GoToIf 1, C205_2_03AC
    pl_CompareVarToValue PVAR_8008, 2
    pl_GoToIf 1, C205_2_03AC
    pl_CompareVarToValue PVAR_8008, 6
    pl_GoToIf 1, C205_2_03AC
    pl_CompareVarToValue PVAR_8008, 5
    pl_GoToIf 1, C205_2_03BE
    pl_CompareVarToValue PVAR_8008, 3
    pl_GoToIf 1, C205_2_03B2
    VMReturn  // End: the sub-script ends

C205_2_03AC:
    pl_PlayFanfare SEQ_ME_ITEM  // Pearl SEQ_FANFA4
    pl_Return

C205_2_03B2:
    pl_PlayFanfare SEQ_ME_WAZA  // Pearl SEQ_WAZA
    pl_Return

C205_2_03B8:
    pl_PlayFanfare SEQ_ME_KEYITEM  // Pearl SEQ_FANFA3
    pl_Return

C205_2_03BE:
    pl_PlayFanfare SEQ_ME_ITEM  // Pearl SEQ_FANFA2
    pl_Return

// ---- Pearl global script 205:39 (a subroutine here)
C205_39_S39:
C205_39_1326:
    pl_Call C205_39_1330
    pl_ReturnCommonScript
    VMReturn  // End: the sub-script ends

C205_39_1330:
    pl_AddVar PVAR_4115, 1
    pl_CompareVarToValue PVAR_4115, 9
    pl_CallIf 4, C205_39_13AD
    pl_CompareVarToValue PVAR_4115, 1
    pl_CallIf 1, C205_39_13B5
    pl_CompareVarToValue PVAR_4115, 2
    pl_CallIf 1, C205_39_13BA
    pl_CompareVarToValue PVAR_4115, 3
    pl_CallIf 1, C205_39_13BF
    pl_CompareVarToValue PVAR_4115, 4
    pl_CallIf 1, C205_39_13C4
    pl_CompareVarToValue PVAR_4115, 5
    pl_CallIf 1, C205_39_13C9
    pl_CompareVarToValue PVAR_4115, 6
    pl_CallIf 1, C205_39_13CE
    pl_CompareVarToValue PVAR_4115, 7
    pl_CallIf 1, C205_39_13D3
    pl_CompareVarToValue PVAR_4115, 8
    pl_CallIf 1, C205_39_13D8
    pl_Return

C205_39_13AD:
    pl_SetVarFromValue PVAR_4115, 1
    pl_Return

C205_39_13B5:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 10  // Pearl bank 199 line 110
    pl_Return

C205_39_13BA:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 11  // Pearl bank 199 line 111
    pl_Return

C205_39_13BF:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 12  // Pearl bank 199 line 112
    pl_Return

C205_39_13C4:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 13  // Pearl bank 199 line 113
    pl_Return

C205_39_13C9:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 14  // Pearl bank 199 line 114
    pl_Return

C205_39_13CE:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 15  // Pearl bank 199 line 115
    pl_Return

C205_39_13D3:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 16  // Pearl bank 199 line 116
    pl_Return

C205_39_13D8:
    MsgWinCloseAll  // another speaker: close the first window
    pl_msg_sys 17  // Pearl bank 199 line 117
    pl_Return

    .balign 4, 0
