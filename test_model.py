import torch
import unittest
import shutil
import os
import glob
from gradescope_utils.autograder_utils.decorators import weight
from gradescope_utils.autograder_utils.files import check_submitted_files
from mingpt.utils import CfgNode as CN

class TestModels(unittest.TestCase):

    @weight(1)
    def test_01_submitted_files(self):
        """[T01] Check submitted files"""
        if os.path.exists('/autograder/submission'):
            # We are running on Gradescope
            print('Submitted files: ', end='')
            print([x.replace('/autograder/submission/', '') for x in
                glob.glob('/autograder/submission/**/*', recursive=True)])
            missing_files = check_submitted_files(['model.py'])
            assert len(missing_files) == 0, f"Missing files: {missing_files}"
            shutil.copy('/autograder/submission/model.py', './mingpt/model.py')
        
    @weight(1)
    def test_02_gqa(self):
        """[T02] Test GroupedQueryAttention"""
        # Wait to import until the files are correctly placed
        from mingpt import model

        torch.manual_seed(3407)

        embedding_dim = 12
        n_query_head = 6

        x_values = [
            [[1.0, 0.5, 0.2, 0.1, -0.3, 0.6, 0.8, -0.5, 0.7, 0.3, 0.2, -0.2], 
            [0.4, -0.1, 0.3, 0.7, 0.1, -0.2, 0.5, -0.4, 0.2, 0.6, -0.1, 0.4]],  # First sequence
            [[-0.5, 0.2, 0.6, -0.3, 0.9, -0.7, 0.1, -0.2, 0.4, 0.5, 0.3, -0.6], 
            [0.9, -0.7, 0.1, -0.2, -0.1, 0.2, 0.8, -0.4, 0.6, 0.3, -0.9, 0.5]]  # Second sequence
        ]

        x = torch.tensor(x_values, dtype=torch.float)
        expected_output_f24_incorrect = torch.tensor([[[-0.6707, -0.0339,  0.1929, -0.0389, -0.6572,  0.3466, -0.3656,
          -0.2566, -0.4334,  0.3029,  0.7416, -0.5442],
         [-0.5875, -0.0559,  0.0638, -0.1880, -0.5565,  0.2202, -0.3040,
          -0.2318, -0.3446,  0.2273,  0.6099, -0.4182]],

        [[-0.3299,  0.0184, -0.0626, -0.2968, -0.6721,  0.4034, -0.4704,
          -0.2333, -0.4571,  0.2939,  0.6875, -0.3060],
         [-0.4378, -0.0135, -0.0247, -0.2471, -0.6021,  0.3199, -0.3881,
          -0.2529, -0.4019,  0.2450,  0.6530, -0.3603]]])

        
        expected_output_f24_correct = torch.tensor([[[ 0.1264,  0.0935,  0.0910,  0.1515, -0.4303,  0.3142,  0.7554,
          -0.0180, -0.0311,  0.2326, -0.0378, -0.2986],
         [ 0.2007,  0.1129,  0.1222,  0.0079, -0.3557,  0.2851,  0.5802,
          -0.0652, -0.0710,  0.1835, -0.0481, -0.3125]],

        [[ 0.1847, -0.0194, -0.0218,  0.2630, -0.1904,  0.4852,  0.6143,
          -0.1469,  0.1620,  0.2659, -0.2455, -0.0866],
         [ 0.1833,  0.0413,  0.0351,  0.1469, -0.2484,  0.3980,  0.5736,
          -0.1203,  0.0895,  0.2163, -0.1682, -0.1800]]])

        C = CN()
        C.system = CN()
        C.system.seed = 3407
        C.system.work_dir = './out/chargpt'
        C.model = model.GPT.get_default_config()
        C.model.block_size = 256
        C.model.n_layer = 6
        C.model.n_query_head = n_query_head
        C.model.n_kv_head = 2
        C.model.n_embd = embedding_dim
        C.model.rope = False
        
        gqa_model = model.GroupedQueryAttention(config=C.model)
        gqa_model.eval()
        q_proj_weight = torch.tensor([[ 0.1495,  0.1324, -0.1786,  0.2149, -0.1697, -0.0976,  0.0825, -0.0122,
          0.1536, -0.0927,  0.0270, -0.1930],
        [-0.1942,  0.2464, -0.1499,  0.0522,  0.1910, -0.0225,  0.0546, -0.1506,
          0.1013, -0.0509, -0.0893,  0.1741],
        [-0.0326,  0.1421, -0.0502, -0.1352, -0.1348, -0.1443, -0.2386, -0.0600,
          0.1657, -0.1679,  0.0962, -0.1611],
        [-0.2336,  0.2884, -0.1868, -0.0934, -0.2771, -0.2533,  0.2239, -0.0142,
         -0.1537,  0.1574,  0.1331, -0.1568],
        [-0.0116,  0.0783,  0.0379,  0.2114, -0.0951,  0.1313,  0.1493, -0.2389,
          0.0303,  0.0731,  0.2167,  0.1184],
        [ 0.1669, -0.0166,  0.2061,  0.0837, -0.1205, -0.0716,  0.2783,  0.1246,
          0.0200,  0.2410,  0.0344, -0.0689],
        [ 0.2267,  0.2540,  0.1753, -0.2534, -0.0389,  0.1234,  0.0366,  0.2209,
         -0.2606, -0.2215, -0.2191, -0.0695],
        [ 0.0674, -0.1963,  0.1960, -0.2694,  0.2195, -0.2688,  0.1962, -0.1949,
         -0.1731, -0.0041,  0.0942,  0.0160],
        [-0.0740, -0.2028, -0.1734, -0.1404,  0.1499, -0.2131, -0.1087, -0.1222,
         -0.0287,  0.0289, -0.1113, -0.2583],
        [ 0.0679,  0.1502,  0.2776,  0.1551,  0.1812, -0.1569, -0.2655, -0.2580,
          0.0594, -0.1308, -0.0465,  0.2260],
        [ 0.0502,  0.1027,  0.1219,  0.0622,  0.1566, -0.0098, -0.1662, -0.2187,
         -0.1832, -0.0513, -0.0250, -0.1741],
        [ 0.1941, -0.2728,  0.0785, -0.1533, -0.0509,  0.2863,  0.1687, -0.1100,
          0.0625, -0.1011,  0.0089, -0.2669]])
        q_proj_bias = torch.tensor([-0.0137,  0.2870, -0.1547,  0.1199,  0.2841, -0.2168, -0.0068,  0.1410,
         0.0323,  0.1082,  0.2443, -0.1128])
        gqa_model.q_proj.weight = torch.nn.Parameter(q_proj_weight)
        gqa_model.q_proj.bias = torch.nn.Parameter(q_proj_bias)

        k_proj_weight = torch.tensor([[-0.0907,  0.2381, -0.1674, -0.1512,  0.1877, -0.0695,  0.0841,  0.0698,
         -0.1113,  0.1902,  0.1769, -0.0341],
        [-0.0699,  0.0711, -0.0979, -0.0419,  0.1254, -0.0760,  0.2109,  0.1727,
         -0.1593, -0.1318, -0.0735,  0.2116],
        [-0.0351, -0.2722,  0.2481, -0.1330, -0.1499, -0.2486,  0.1404, -0.0627,
         -0.0567,  0.1426, -0.0241, -0.1208],
        [ 0.0656, -0.2012, -0.0790,  0.1376,  0.0991,  0.2098,  0.2038,  0.1131,
          0.1569, -0.1293,  0.0624,  0.0982]])
        k_proj_bias = torch.tensor([-0.2841, -0.1966,  0.0917,  0.0586])

        gqa_model.k_proj.weight = torch.nn.Parameter(k_proj_weight)
        gqa_model.k_proj.bias = torch.nn.Parameter(k_proj_bias)

        v_proj_weight = torch.tensor([[-0.2421, -0.0985, -0.0801,  0.0967, -0.1813,  0.2452,  0.2555, -0.2769,
         -0.2492,  0.0392, -0.0826, -0.2043],
        [-0.0322, -0.1496,  0.0130, -0.2461, -0.0065,  0.2298,  0.0895, -0.1140,
          0.1781,  0.2201,  0.2061, -0.2536],
        [ 0.2770,  0.1927, -0.0198,  0.2248, -0.1363, -0.1802,  0.1956, -0.0422,
         -0.0826, -0.2062, -0.1227, -0.1068],
        [-0.1452, -0.1286,  0.0277,  0.2578,  0.1878,  0.1314,  0.1801,  0.1107,
          0.2759, -0.1299,  0.2254,  0.2631]])
        v_proj_bias = torch.tensor([-0.0012,  0.1807,  0.0342, -0.2545])

        gqa_model.v_proj.weight = torch.nn.Parameter(v_proj_weight)
        gqa_model.v_proj.bias = torch.nn.Parameter(v_proj_bias)

        out_proj_weight = torch.tensor([[-0.0602, -0.2096, -0.4599, -0.1434],
        [-0.3830,  0.0451,  0.1252, -0.2059],
        [-0.2889,  0.4688,  0.4549,  0.2245],
        [ 0.4431,  0.4093,  0.1395, -0.1696],
        [ 0.1992, -0.4882,  0.0165, -0.2074],
        [ 0.1315,  0.4580, -0.1988, -0.2369],
        [ 0.2098, -0.2978,  0.1014,  0.0181],
        [-0.4149,  0.0854,  0.1087,  0.4946],
        [ 0.3568, -0.3117, -0.1142,  0.1734],
        [-0.3415,  0.3934,  0.1010,  0.2619],
        [-0.2150,  0.3843,  0.1724, -0.3474],
        [-0.0044, -0.2749, -0.3643,  0.3182]])
        out_proj_bias = torch.tensor([-0.3728, -0.1078, -0.2076, -0.4204, -0.4274,  0.0972, -0.2473, -0.2221,
        -0.2062,  0.1064,  0.4010, -0.1717])

        out_proj_weight_correct = torch.tensor([[-3.4733e-02, -1.2103e-01, -2.6552e-01, -8.2804e-02, -2.2114e-01,
          2.6023e-02,  7.2272e-02, -1.1889e-01, -1.6681e-01,  2.7069e-01,
          2.6264e-01,  1.2963e-01],
        [ 2.5580e-01,  2.3628e-01,  8.0559e-02, -9.7899e-02,  1.1503e-01,
         -2.8184e-01,  9.5119e-03, -1.1977e-01,  7.5920e-02,  2.6445e-01,
         -1.1479e-01, -1.3677e-01],
        [ 1.2111e-01, -1.7193e-01,  5.8549e-02,  1.0436e-02, -2.3953e-01,
          4.9291e-02,  6.2748e-02,  2.8555e-01,  2.0600e-01, -1.7997e-01,
         -6.5935e-02,  1.0011e-01],
        [-1.9716e-01,  2.2714e-01,  5.8316e-02,  1.5121e-01, -1.2413e-01,
          2.2185e-01,  9.9534e-02, -2.0059e-01, -2.5238e-03, -1.5874e-01,
         -2.1036e-01,  1.8369e-01],
        [-2.1526e-01, -6.2245e-02, -1.1988e-01, -2.4273e-01, -2.4677e-01,
          5.6112e-02, -1.4276e-01, -1.2823e-01, -1.1905e-01,  6.1430e-02,
          2.3149e-01, -9.9122e-02],
        [-1.8955e-01,  5.1829e-02, -1.5957e-01,  1.5637e-01, -7.2252e-02,
         -7.1848e-02, -2.7398e-02, -1.6563e-01, -1.6741e-01,  2.4665e-01,
          1.3737e-01, -2.6937e-01],
        [-1.7923e-01,  1.7367e-01, -2.7625e-01,  2.5979e-01, -4.6381e-02,
          2.1984e-01,  2.0330e-01,  3.2518e-02,  4.1915e-05, -2.8044e-01,
          1.7456e-01,  2.4966e-01],
        [-3.4290e-03,  6.2335e-02, -8.3135e-02, -6.7679e-02, -1.5093e-01,
          2.0324e-01,  1.9377e-01,  1.4504e-01, -1.6936e-01, -3.6507e-02,
          2.4756e-01,  9.6110e-02],
        [ 9.3247e-02, -1.3633e-01,  2.2774e-01,  3.4240e-03, -2.4491e-01,
          1.8305e-01, -1.3641e-01, -2.8363e-01,  7.6847e-02, -1.4959e-01,
         -2.2599e-01, -1.8621e-01],
        [-1.2558e-01, -8.5607e-02, -2.7345e-02,  2.2584e-01, -1.7493e-01,
          1.1801e-01,  6.9361e-02, -1.2863e-01,  1.2311e-01,  2.2484e-01,
         -1.2688e-01, -9.8285e-03],
        [ 2.6320e-01,  1.7636e-01,  1.2234e-01,  8.4611e-02, -2.3949e-01,
         -2.3751e-01, -9.5439e-02,  7.4756e-02,  3.5583e-02,  7.9555e-02,
          2.8094e-01,  1.2355e-01],
        [-9.1161e-02,  1.3756e-01,  1.6890e-01,  8.2898e-02, -2.5251e-01,
         -1.8564e-02, -1.2917e-01,  1.7565e-01, -2.5932e-01, -1.2290e-01,
          1.0364e-01,  4.1356e-02]])
        
        out_proj_bias_correct = torch.tensor([ 0.2691,  0.1451,  0.1171, -0.1659, -0.2344,  0.2680,  0.2594, -0.1885,
        -0.0597,  0.1000, -0.1104, -0.2673])
        _, B = gqa_model.out_proj.weight.shape
        
        if B == 12:
            # If output projection dim matches, check with expected_output_f24_correct (not summation approach)
            gqa_model.out_proj.weight = torch.nn.Parameter(out_proj_weight_correct)
            gqa_model.out_proj.bias = torch.nn.Parameter(out_proj_bias_correct)
            output, *_ = gqa_model(x)
            torch.testing.assert_close(output, expected_output_f24_correct, atol=1e-3, rtol=1e-3)
        else:
            # If output projection dim doesn't match, check with expected_output_f24 (summation approach)
            gqa_model.out_proj.weight = torch.nn.Parameter(out_proj_weight)
            gqa_model.out_proj.bias = torch.nn.Parameter(out_proj_bias)
            output, *_ = gqa_model(x)
            torch.testing.assert_close(output, expected_output_f24_incorrect, atol=1e-3, rtol=1e-3)

    @weight(2)
    def test_03_rope(self):
        """[T03] Test RotaryPositionalEmbeddings"""
        # Wait to import until the files are correctly placed
        from mingpt import model
        
        torch.manual_seed(3407)
        embedding_dim = 4 
        x = torch.tensor([[[[1.0, 0.8], [0.5, 0.3], [-0.2, 0.1], [0.4, 0.5]], [[0.4, 0.1], [-0.1, -0.6], [0.7, 0.4], [0.3, -0.1]]]], dtype=torch.float)
        C = CN()
        C.system = CN()
        C.system.seed = 3407
        C.system.work_dir = './out/chargpt'
        C.model = model.GPT.get_default_config()
        C.model.block_size = 256
        C.model.n_layer = 6
        C.model.n_kv_head = 2
        C.model.n_embd = embedding_dim
        C.model.embedding_dim = embedding_dim
        C.model.base = 10000 
        C.model.rope = True

        rope_model = model.RotaryPositionalEmbeddings(d=C.model.embedding_dim//C.model.n_kv_head, base=C.model.base)
        
        expected_output = torch.tensor([[[[-0.1329,  1.2737],
          [-0.4809,  0.3298],
          [ 0.1839, -0.1272],
          [ 0.1169, -0.6295]],

         [[ 0.1320,  0.3906],
          [ 0.5872,  0.1588],
          [-0.7494, -0.2972],
          [-0.2718, -0.1617]]]])
        torch.manual_seed(3407)
        output = rope_model(x)
        torch.testing.assert_close(output, expected_output, atol=1e-4, rtol=1e-4)
    
    @weight(1)
    def test_04_gqa(self):
        """[T04] Test GroupedQueryAttention with Dropout"""
        # Wait to import until the files are correctly placed
        from mingpt import model

        torch.manual_seed(3407)

        embedding_dim = 12
        n_query_head = 6

        x_values = [
            [[1.0, 0.5, 0.2, 0.1, -0.3, 0.6, 0.8, -0.5, 0.7, 0.3, 0.2, -0.2], 
            [0.4, -0.1, 0.3, 0.7, 0.1, -0.2, 0.5, -0.4, 0.2, 0.6, -0.1, 0.4]],  # First sequence
            [[-0.5, 0.2, 0.6, -0.3, 0.9, -0.7, 0.1, -0.2, 0.4, 0.5, 0.3, -0.6], 
            [0.9, -0.7, 0.1, -0.2, -0.1, 0.2, 0.8, -0.4, 0.6, 0.3, -0.9, 0.5]]  # Second sequence
        ]

        x = torch.tensor(x_values, dtype=torch.float)

        C = CN()
        C.system = CN()
        C.system.seed = 3407
        C.system.work_dir = './out/chargpt'
        C.model = model.GPT.get_default_config()
        C.model.block_size = 256
        C.model.n_layer = 6
        C.model.n_query_head = n_query_head
        C.model.n_kv_head = 2
        C.model.n_embd = embedding_dim
        C.model.rope = False
        
        gqa_model_without_dropout = model.GroupedQueryAttention(config=C.model)
        gqa_model_without_dropout.eval()
        C.model.attn_pdrop = 0.9
        C.model.resid_pdrop = 0
        gqa_model_without_resid_dropout = model.GroupedQueryAttention(config=C.model)
        C.model.resid_pdrop = 0.9
        C.model.attn_pdrop = 0
        gqa_model_without_attn_dropout = model.GroupedQueryAttention(config=C.model)

        q_proj_weight = torch.tensor([[ 0.1495,  0.1324, -0.1786,  0.2149, -0.1697, -0.0976,  0.0825, -0.0122,
          0.1536, -0.0927,  0.0270, -0.1930],
        [-0.1942,  0.2464, -0.1499,  0.0522,  0.1910, -0.0225,  0.0546, -0.1506,
          0.1013, -0.0509, -0.0893,  0.1741],
        [-0.0326,  0.1421, -0.0502, -0.1352, -0.1348, -0.1443, -0.2386, -0.0600,
          0.1657, -0.1679,  0.0962, -0.1611],
        [-0.2336,  0.2884, -0.1868, -0.0934, -0.2771, -0.2533,  0.2239, -0.0142,
         -0.1537,  0.1574,  0.1331, -0.1568],
        [-0.0116,  0.0783,  0.0379,  0.2114, -0.0951,  0.1313,  0.1493, -0.2389,
          0.0303,  0.0731,  0.2167,  0.1184],
        [ 0.1669, -0.0166,  0.2061,  0.0837, -0.1205, -0.0716,  0.2783,  0.1246,
          0.0200,  0.2410,  0.0344, -0.0689],
        [ 0.2267,  0.2540,  0.1753, -0.2534, -0.0389,  0.1234,  0.0366,  0.2209,
         -0.2606, -0.2215, -0.2191, -0.0695],
        [ 0.0674, -0.1963,  0.1960, -0.2694,  0.2195, -0.2688,  0.1962, -0.1949,
         -0.1731, -0.0041,  0.0942,  0.0160],
        [-0.0740, -0.2028, -0.1734, -0.1404,  0.1499, -0.2131, -0.1087, -0.1222,
         -0.0287,  0.0289, -0.1113, -0.2583],
        [ 0.0679,  0.1502,  0.2776,  0.1551,  0.1812, -0.1569, -0.2655, -0.2580,
          0.0594, -0.1308, -0.0465,  0.2260],
        [ 0.0502,  0.1027,  0.1219,  0.0622,  0.1566, -0.0098, -0.1662, -0.2187,
         -0.1832, -0.0513, -0.0250, -0.1741],
        [ 0.1941, -0.2728,  0.0785, -0.1533, -0.0509,  0.2863,  0.1687, -0.1100,
          0.0625, -0.1011,  0.0089, -0.2669]])
        q_proj_bias = torch.tensor([-0.0137,  0.2870, -0.1547,  0.1199,  0.2841, -0.2168, -0.0068,  0.1410,
         0.0323,  0.1082,  0.2443, -0.1128])

        gqa_model_without_dropout.q_proj.weight = torch.nn.Parameter(q_proj_weight)
        gqa_model_without_dropout.q_proj.bias = torch.nn.Parameter(q_proj_bias)

        gqa_model_without_resid_dropout.q_proj.weight = torch.nn.Parameter(q_proj_weight)
        gqa_model_without_resid_dropout.q_proj.bias = torch.nn.Parameter(q_proj_bias)

        gqa_model_without_attn_dropout.q_proj.weight = torch.nn.Parameter(q_proj_weight)
        gqa_model_without_attn_dropout.q_proj.bias = torch.nn.Parameter(q_proj_bias)
        

        k_proj_weight = torch.tensor([[-0.0907,  0.2381, -0.1674, -0.1512,  0.1877, -0.0695,  0.0841,  0.0698,
         -0.1113,  0.1902,  0.1769, -0.0341],
        [-0.0699,  0.0711, -0.0979, -0.0419,  0.1254, -0.0760,  0.2109,  0.1727,
         -0.1593, -0.1318, -0.0735,  0.2116],
        [-0.0351, -0.2722,  0.2481, -0.1330, -0.1499, -0.2486,  0.1404, -0.0627,
         -0.0567,  0.1426, -0.0241, -0.1208],
        [ 0.0656, -0.2012, -0.0790,  0.1376,  0.0991,  0.2098,  0.2038,  0.1131,
          0.1569, -0.1293,  0.0624,  0.0982]])
        k_proj_bias = torch.tensor([-0.2841, -0.1966,  0.0917,  0.0586])

        gqa_model_without_dropout.k_proj.weight = torch.nn.Parameter(k_proj_weight)
        gqa_model_without_dropout.k_proj.bias = torch.nn.Parameter(k_proj_bias)

        gqa_model_without_resid_dropout.k_proj.weight = torch.nn.Parameter(k_proj_weight)
        gqa_model_without_resid_dropout.k_proj.bias = torch.nn.Parameter(k_proj_bias)

        gqa_model_without_attn_dropout.k_proj.weight = torch.nn.Parameter(k_proj_weight)
        gqa_model_without_attn_dropout.k_proj.bias = torch.nn.Parameter(k_proj_bias)

        v_proj_weight = torch.tensor([[-0.2421, -0.0985, -0.0801,  0.0967, -0.1813,  0.2452,  0.2555, -0.2769,
         -0.2492,  0.0392, -0.0826, -0.2043],
        [-0.0322, -0.1496,  0.0130, -0.2461, -0.0065,  0.2298,  0.0895, -0.1140,
          0.1781,  0.2201,  0.2061, -0.2536],
        [ 0.2770,  0.1927, -0.0198,  0.2248, -0.1363, -0.1802,  0.1956, -0.0422,
         -0.0826, -0.2062, -0.1227, -0.1068],
        [-0.1452, -0.1286,  0.0277,  0.2578,  0.1878,  0.1314,  0.1801,  0.1107,
          0.2759, -0.1299,  0.2254,  0.2631]])
        v_proj_bias = torch.tensor([-0.0012,  0.1807,  0.0342, -0.2545])

        gqa_model_without_dropout.v_proj.weight = torch.nn.Parameter(v_proj_weight)
        gqa_model_without_dropout.v_proj.bias = torch.nn.Parameter(v_proj_bias)

        gqa_model_without_resid_dropout.v_proj.weight = torch.nn.Parameter(v_proj_weight)
        gqa_model_without_resid_dropout.v_proj.bias = torch.nn.Parameter(v_proj_bias)

        gqa_model_without_attn_dropout.v_proj.weight = torch.nn.Parameter(v_proj_weight)
        gqa_model_without_attn_dropout.v_proj.bias = torch.nn.Parameter(v_proj_bias)

        out_proj_weight = torch.tensor([[-0.0602, -0.2096, -0.4599, -0.1434],
        [-0.3830,  0.0451,  0.1252, -0.2059],
        [-0.2889,  0.4688,  0.4549,  0.2245],
        [ 0.4431,  0.4093,  0.1395, -0.1696],
        [ 0.1992, -0.4882,  0.0165, -0.2074],
        [ 0.1315,  0.4580, -0.1988, -0.2369],
        [ 0.2098, -0.2978,  0.1014,  0.0181],
        [-0.4149,  0.0854,  0.1087,  0.4946],
        [ 0.3568, -0.3117, -0.1142,  0.1734],
        [-0.3415,  0.3934,  0.1010,  0.2619],
        [-0.2150,  0.3843,  0.1724, -0.3474],
        [-0.0044, -0.2749, -0.3643,  0.3182]])
        out_proj_bias = torch.tensor([-0.3728, -0.1078, -0.2076, -0.4204, -0.4274,  0.0972, -0.2473, -0.2221,
        -0.2062,  0.1064,  0.4010, -0.1717])

        out_proj_weight_correct = torch.tensor([[-3.4733e-02, -1.2103e-01, -2.6552e-01, -8.2804e-02, -2.2114e-01,
          2.6023e-02,  7.2272e-02, -1.1889e-01, -1.6681e-01,  2.7069e-01,
          2.6264e-01,  1.2963e-01],
        [ 2.5580e-01,  2.3628e-01,  8.0559e-02, -9.7899e-02,  1.1503e-01,
         -2.8184e-01,  9.5119e-03, -1.1977e-01,  7.5920e-02,  2.6445e-01,
         -1.1479e-01, -1.3677e-01],
        [ 1.2111e-01, -1.7193e-01,  5.8549e-02,  1.0436e-02, -2.3953e-01,
          4.9291e-02,  6.2748e-02,  2.8555e-01,  2.0600e-01, -1.7997e-01,
         -6.5935e-02,  1.0011e-01],
        [-1.9716e-01,  2.2714e-01,  5.8316e-02,  1.5121e-01, -1.2413e-01,
          2.2185e-01,  9.9534e-02, -2.0059e-01, -2.5238e-03, -1.5874e-01,
         -2.1036e-01,  1.8369e-01],
        [-2.1526e-01, -6.2245e-02, -1.1988e-01, -2.4273e-01, -2.4677e-01,
          5.6112e-02, -1.4276e-01, -1.2823e-01, -1.1905e-01,  6.1430e-02,
          2.3149e-01, -9.9122e-02],
        [-1.8955e-01,  5.1829e-02, -1.5957e-01,  1.5637e-01, -7.2252e-02,
         -7.1848e-02, -2.7398e-02, -1.6563e-01, -1.6741e-01,  2.4665e-01,
          1.3737e-01, -2.6937e-01],
        [-1.7923e-01,  1.7367e-01, -2.7625e-01,  2.5979e-01, -4.6381e-02,
          2.1984e-01,  2.0330e-01,  3.2518e-02,  4.1915e-05, -2.8044e-01,
          1.7456e-01,  2.4966e-01],
        [-3.4290e-03,  6.2335e-02, -8.3135e-02, -6.7679e-02, -1.5093e-01,
          2.0324e-01,  1.9377e-01,  1.4504e-01, -1.6936e-01, -3.6507e-02,
          2.4756e-01,  9.6110e-02],
        [ 9.3247e-02, -1.3633e-01,  2.2774e-01,  3.4240e-03, -2.4491e-01,
          1.8305e-01, -1.3641e-01, -2.8363e-01,  7.6847e-02, -1.4959e-01,
         -2.2599e-01, -1.8621e-01],
        [-1.2558e-01, -8.5607e-02, -2.7345e-02,  2.2584e-01, -1.7493e-01,
          1.1801e-01,  6.9361e-02, -1.2863e-01,  1.2311e-01,  2.2484e-01,
         -1.2688e-01, -9.8285e-03],
        [ 2.6320e-01,  1.7636e-01,  1.2234e-01,  8.4611e-02, -2.3949e-01,
         -2.3751e-01, -9.5439e-02,  7.4756e-02,  3.5583e-02,  7.9555e-02,
          2.8094e-01,  1.2355e-01],
        [-9.1161e-02,  1.3756e-01,  1.6890e-01,  8.2898e-02, -2.5251e-01,
         -1.8564e-02, -1.2917e-01,  1.7565e-01, -2.5932e-01, -1.2290e-01,
          1.0364e-01,  4.1356e-02]])
        
        out_proj_bias_correct = torch.tensor([ 0.2691,  0.1451,  0.1171, -0.1659, -0.2344,  0.2680,  0.2594, -0.1885,
        -0.0597,  0.1000, -0.1104, -0.2673])

        _, B = gqa_model_without_dropout.out_proj.weight.shape
        if B == 12:
          gqa_model_without_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight_correct)
          gqa_model_without_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias_correct)
          output_without_dropout, *_ = gqa_model_without_dropout(x)

          gqa_model_without_resid_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight_correct)
          gqa_model_without_resid_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias_correct)
          output_without_resid_dropout, *_ = gqa_model_without_resid_dropout(x)

          gqa_model_without_attn_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight_correct)
          gqa_model_without_attn_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias_correct)
          output_without_attn_dropout, *_ = gqa_model_without_attn_dropout(x)
        else:
          gqa_model_without_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight)
          gqa_model_without_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias)
          output_without_dropout, *_ = gqa_model_without_dropout(x)

          gqa_model_without_resid_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight)
          gqa_model_without_resid_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias)
          output_without_resid_dropout, *_ = gqa_model_without_resid_dropout(x)

          gqa_model_without_attn_dropout.out_proj.weight = torch.nn.Parameter(out_proj_weight)
          gqa_model_without_attn_dropout.out_proj.bias = torch.nn.Parameter(out_proj_bias)
          output_without_attn_dropout, *_ = gqa_model_without_attn_dropout(x)

        try:
          torch.testing.assert_close(output_without_dropout, output_without_resid_dropout)
        except AssertionError:
          try:
            torch.testing.assert_close(output_without_dropout, output_without_attn_dropout)
          except AssertionError:
            return  # Tensors are different as expected
          raise AssertionError("Some or all dropout layers are not being applied.")
        
        raise AssertionError("Some or all dropout layers are not being applied.")

if __name__ == '__main__':
    unittest.main(buffer=False)
